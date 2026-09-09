import streamlit as st
import json
import websocket
import pandas as pd
import time

class BulkRegLogHealthChecker:
    """
    Class xử lý kết nối WebSocket hỗ trợ ping check hàng loạt (Batch Execution).
    Mục đích: Save effort tối đa cho QC. Thay vì test lặp đi lặp lại từng domain,
    class này sẽ xử lý danh sách hàng chục/trăm endpoints chỉ với 1 cú click.
    Tích hợp cơ chế Fail-fast (timeout) để không làm block toàn bộ tiến trình nếu 1 server down.
    """
    
    def verify_single_endpoint(self, ws_url, action, username, password):
        """
        Thực thi test trên một endpoint cụ thể.
        Đã bổ sung cơ chế Auto-Sanitize URL để chặn Defect do Human Error.
        """
        # [NEW UPDATE] Tự động chuẩn hóa Test Data (Protocol scheme)
        ws_url = ws_url.strip()
        if ws_url.startswith("https://"):
            ws_url = ws_url.replace("https://", "wss://", 1)
            print(f"[Info] Auto-converted scheme to: {ws_url}")
        elif ws_url.startswith("http://"):
            ws_url = ws_url.replace("http://", "ws://", 1)
            
        try:
            # Set timeout (VD: 5s) để tránh treo script (Bottleneck)
            ws = websocket.create_connection(ws_url, timeout=5)
            
            payload = {
                "action": action,
                "data": {"user": username, "pass": password}
            }
            
            ws.send(json.dumps(payload))
            response_raw = ws.recv()
            ws.close()
            
            return "Passed", response_raw
        except websocket.WebSocketTimeoutException:
            return "Failed (Timeout)", "Server không phản hồi sau 5s."
        except Exception as e:
            return "Failed (Error)", f"Lỗi kết nối: {str(e)}"

def render_bulk_health_check_ui():
    """
    UI dành cho luồng Batch Execution.
    Hỗ trợ input nhiều URLs cùng lúc và xuất kết quả ra bảng Dataframe trực quan.
    """
    st.set_page_config(page_title="Bulk QC Health Check", page_icon="⚡", layout="wide")
    
    st.title("⚡ Canvas QA - Bulk Reg/Log Health Check")
    st.markdown("Tool hỗ trợ verify **Happy path** hàng loạt cho nhiều Domain/Endpoint cùng lúc. Giúp team giảm thiểu manual **Effort** khi Release nhiều site.")

    with st.form("bulk_health_check_form"):
        st.subheader("1. Danh sách Test Environment (Endpoints)")
        # Field mới: Text area cho phép nhập nhiều dòng
        urls_input = st.text_area(
            "Nhập danh sách WebSocket URLs (Mỗi URL một dòng):", 
            value="wss://game1.client-server.com/ws\nwss://game2.client-server.com/ws",
            height=150
        )
        
        st.subheader("2. Test Data & Scenario")
        action = st.radio("Tính năng cần test (Test Scenario)", ["login", "register"], horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", value="qc_tester_bulk")
        with col2:
            password = st.text_input("Password", value="123456", type="password")
            
        submit_btn = st.form_submit_button("🚀 Start Bulk Execution")

    if submit_btn:
        # Xử lý data đầu vào: tách dòng, xóa khoảng trắng, loại bỏ dòng trống
        ws_urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        total_urls = len(ws_urls)
        
        if total_urls == 0:
            st.warning("⚠️ Vui lòng nhập ít nhất 1 URL để chạy test.")
            return

        st.info(f"Đang khởi chạy luồng Test Execution cho **{total_urls}** endpoints. Vui lòng chờ...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        checker = BulkRegLogHealthChecker()
        results = []
        
        # Vòng lặp chạy qua từng URL
        for idx, url in enumerate(ws_urls):
            status_text.text(f"Executing ({idx + 1}/{total_urls}): Đang ping {url} ...")
            
            status, raw_resp = checker.verify_single_endpoint(url, action, username, password)
            
            results.append({
                "ID": idx + 1,
                "Endpoint URL": url,
                "Action": action.upper(),
                "Status": status,
                "Actual Result (Raw)": raw_resp
            })
            
            progress_bar.progress((idx + 1) / total_urls)
            
            # Delay nhẹ 0.5s giữa các URL để hệ thống mượt mà, không giật lag mạng nội bộ
            time.sleep(0.5)
            
        st.success(f"✅ Bulk Execution Completed! Đã test xong {total_urls} endpoints.")
        
        # Hiển thị Test Summary dưới dạng Table
        df_results = pd.DataFrame(results)
        
        # Highlight màu mè chút cho QC dễ nhìn Defect
        def color_status(val):
            color = 'green' if 'Passed' in val else 'red'
            return f'color: {color}; font-weight: bold'
            
        styled_df = df_results.style.map(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Export ra file để đính kèm Report
        csv = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Bug Report (.CSV)",
            data=csv,
            file_name='bulk_health_check_report.csv',
            mime='text/csv',
        )
render_bulk_health_check_ui()
