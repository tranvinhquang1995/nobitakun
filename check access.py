import streamlit as st
import asyncio
import aiohttp
from urllib.parse import urlparse
import pandas as pd
import time
import tldextract

# Hàm chuẩn hóa URL đầu vào
def normalize_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if not raw_url:
        return ""
    if not raw_url.startswith(("http://", "https://")):
        return f"https://{raw_url}"
    return raw_url

# Hàm trích xuất domain chính (root domain hoặc registered domain)
def extract_domain(url: str) -> str:
    try:
        extracted = tldextract.extract(url)
        if extracted.registered_domain:
            return extracted.registered_domain
        return urlparse(url).netloc
    except Exception:
        return urlparse(url).netloc

# Worker kiểm tra 1 URL
async def check_url_access(session: aiohttp.ClientSession, original_url: str, timeout_sec: int = 10):
    norm_url = normalize_url(original_url)
    if not norm_url:
        return None

    orig_domain = extract_domain(norm_url)
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    
    try:
        # allow_redirects=True để tự động theo vết các bước chuyển hướng
        async with session.get(norm_url, timeout=timeout, allow_redirects=True, ssl=False) as response:
            final_url = str(response.url)
            final_domain = extract_domain(final_url)
            status_code = response.status
            
            # Kiểm tra xem có redirect hay không
            history = response.history
            is_redirected = len(history) > 0 or (norm_url.rstrip("/") != final_url.rstrip("/"))
            
            redirect_chain = [str(h.url) for h in history] + [final_url] if len(history) > 0 else []
            
            # Đánh giá khả năng truy cập
            access_status = "Access OK" if status_code < 400 else f"HTTP Error {status_code}"

            return {
                "Input URL": original_url,
                "Origin Domain": orig_domain,
                "Access Status": access_status,
                "Final HTTP Code": status_code,
                "Is Redirected": "Yes" if is_redirected else "No",
                "Final URL": final_url,
                "Final Domain": final_domain,
                "Redirect Steps": len(history),
                "Redirect Chain": " ➔ ".join(redirect_chain) if redirect_chain else "None"
            }
            
    except asyncio.TimeoutError:
        return {
            "Input URL": original_url,
            "Origin Domain": orig_domain,
            "Access Status": "Timeout (Hết thời gian chờ)",
            "Final HTTP Code": None,
            "Is Redirected": "Unknown",
            "Final URL": "",
            "Final Domain": "",
            "Redirect Steps": 0,
            "Redirect Chain": "Error"
        }
    except aiohttp.ClientConnectorError as e:
        return {
            "Input URL": original_url,
            "Origin Domain": orig_domain,
            "Access Status": "Connection Failed (Domain chết / Lỗi DNS / Tắt server)",
            "Final HTTP Code": None,
            "Is Redirected": "No",
            "Final URL": "",
            "Final Domain": "",
            "Redirect Steps": 0,
            "Redirect Chain": "Error"
        }
    except Exception as e:
        return {
            "Input URL": original_url,
            "Origin Domain": orig_domain,
            "Access Status": f"Lỗi: {type(e).__name__}",
            "Final HTTP Code": None,
            "Is Redirected": "Unknown",
            "Final URL": "",
            "Final Domain": "",
            "Redirect Steps": 0,
            "Redirect Chain": "Error"
        }

# Quản lý hàng đợi request
async def process_batch(urls, concurrency_limit, timeout_sec):
    connector = aiohttp.TCPConnector(limit=concurrency_limit, verify_ssl=False)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [check_url_access(session, url, timeout_sec) for url in urls]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Bulk Domain Access & Redirect Checker", layout="wide")

st.title("🌐 Bulk Domain Access & Redirect Checker")
st.write("Công cụ kiểm tra trạng thái sống/chết và theo dõi domain đích chuyển hướng (Redirect Chain) hàng loạt.")

# Cột cấu hình
with st.sidebar:
    st.header("⚙️ Cấu hình quét")
    concurrency = st.slider("Số request đồng thời (Concurrency):", min_value=5, max_value=100, value=30, step=5,
                           help="Tăng tốc độ kiểm tra. Giá trị 30-50 là mức an toàn tránh bị nghẽn mạng máy chủ.")
    timeout_val = st.slider("Thời gian timeout mỗi URL (giây):", min_value=3, max_value=30, value=10, step=1)
    
    st.markdown("---")
    st.markdown("**Ghi chú kết quả:**")
    st.markdown("- **Origin Domain**: Domain gốc ban đầu.")
    st.markdown("- **Final Domain**: Domain đích sau khi chuyển hướng.")
    st.markdown("- **Redirect Chain**: Chuỗi các URL đã nhảy qua.")

# Nhận dữ liệu đầu vào
tab1, tab2 = st.tabs(["📝 Nhập trực tiếp danh sách", "📁 Tải file danh sách (TXT / CSV)"])

input_urls = []

with tab1:
    text_input = st.text_area(
        "Nhập danh sách domain hoặc URL (mỗi dòng một link):",
        placeholder="example.com\nhttp://facebook.com\nred88.navy/slots\nkts9944.com",
        height=200
    )
    if text_input.strip():
        input_urls = [line.strip() for line in text_input.splitlines() if line.strip()]

with tab2:
    uploaded_file = st.file_uploader("Tải file danh sách (.txt hoặc .csv):", type=["txt", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
            input_urls = [line.strip() for line in content.splitlines() if line.strip()]
        elif uploaded_file.name.endswith(".csv"):
            df_upload = pd.read_csv(uploaded_file)
            st.write("Xem trước file:", df_upload.head(3))
            selected_col = st.selectbox("Chọn cột chứa URL/Domain:", df_upload.columns)
            input_urls = df_upload[selected_col].dropna().astype(str).str.strip().tolist()

# Xử lý khi nhấn nút Quét
if st.button("🚀 Bắt đầu kiểm tra", type="primary"):
    if not input_urls:
        st.warning("Vui lòng nhập ít nhất 1 URL hoặc tải file lên!")
    else:
        # Loại bỏ các dòng trùng lặp nhưng vẫn giữ nguyên thứ tự
        unique_urls = list(dict.fromkeys(input_urls))
        st.info(f"Đang tiến hành kiểm tra {len(unique_urls)} link (đã loại bỏ trùng lặp)...")
        
        start_time = time.time()
        
        # Xử lý Event Loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        with st.spinner("Đang gửi request và phân tích redirect..."):
            raw_results = loop.run_until_complete(process_batch(unique_urls, concurrency, timeout_val))
            
        elapsed_time = time.time() - start_time
        df_result = pd.DataFrame(raw_results)
        
        # Thống kê nhanh
        st.success(f"✅ Hoàn thành quét {len(unique_urls)} URLs trong {elapsed_time:.2f} giây!")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        total_ok = (df_result["Access Status"] == "Access OK").sum()
        total_redirect = (df_result["Is Redirected"] == "Yes").sum()
        total_error = len(df_result) - total_ok
        
        col_m1.metric("Tổng số URL", len(df_result))
        col_m2.metric("Truy cập thành công", total_ok)
        col_m3.metric("Có chuyển hướng (Redirect)", total_redirect)
        col_m4.metric("Lỗi / Không truy cập được", total_error)
        
        # Bộ lọc nhanh kết quả
        filter_option = st.radio("Lọc danh sách hiển thị:", ["Tất cả", "Chỉ URL có Redirect", "Chỉ URL Lỗi"], horizontal=True)
        if filter_option == "Chỉ URL có Redirect":
            display_df = df_result[df_result["Is Redirected"] == "Yes"]
        elif filter_option == "Chỉ URL Lỗi":
            display_df = df_result[df_result["Access Status"] != "Access OK"]
        else:
            display_df = df_result

        st.dataframe(display_df, use_container_width=True)
        
        # Tải file kết quả
        c1, c2 = st.columns(2)
        with c1:
            csv_data = df_result.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="⬇️ Tải kết quả về dạng CSV",
                data=csv_data,
                file_name="domain_access_results.csv",
                mime="text/csv"
            )
