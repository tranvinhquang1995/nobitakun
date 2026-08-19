import streamlit as st
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import time

# --- HÀM BẤT ĐỒNG BỘ ĐỂ LẤY DỮ LIỆU ---
async def fetch_title(session, kts_number, base_url):
    url = base_url.format(kts_number)
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, timeout=timeout) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                title = soup.title.string if soup.title else "Không tìm thấy Title"
                return {"KTS": f"kts{kts_number}", "Title": title.strip(), "Status": "Thành công", "URL": url}
            else:
                return {"KTS": f"kts{kts_number}", "Title": "", "Status": f"Lỗi HTTP {response.status}", "URL": url}
    except Exception as e:
        return {"KTS": f"kts{kts_number}", "Title": "", "Status": f"Thất bại: {str(e)}", "URL": url}

async def run_scraper(start, end, base_url):
    # Giới hạn 50 request song song để không bị server block
    connector = aiohttp.TCPConnector(limit=50)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [fetch_title(session, i, base_url) for i in range(start, end + 1)]
        responses = await asyncio.gather(*tasks)
        return responses

# --- GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Tool Check Title URL", layout="wide")

st.title("🔗 Tool Lấy Title Hàng Loạt Từ URL")
st.write("Nhập thông số URL bên dưới. Ký tự `{}` trong link sẽ được thay thế bằng các số KTS.")

# Cấu hình đầu vào
default_url = "https://games.mt-sta.com/kts{}/?token=10-79494e8719042225c0a3bc9a89e42e29&ru=https://red88.navy/slots"
base_url = st.text_input("Đường dẫn gốc (Sử dụng {} để làm biến số):", value=default_url)

col1, col2 = st.columns(2)
with col1:
    start_num = st.number_input("Bắt đầu từ số:", min_value=1, value=9800, step=1)
with col2:
    end_num = st.number_input("Đến số:", min_value=1, value=9999, step=1)

if st.button("🚀 Bắt Đầu Quét"):
    if "{}" not in base_url:
        st.error("Lỗi: Đường dẫn gốc phải chứa ký tự `{}` để thay thế biến số!")
    elif start_num > end_num:
        st.error("Lỗi: Số bắt đầu không thể lớn hơn số kết thúc!")
    else:
        st.info(f"Đang tiến hành quét {end_num - start_num + 1} links. Vui lòng đợi...")
        start_time = time.time()
        
        # Xử lý event loop cho Streamlit (tránh lỗi asyncio RuntimeError)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Chạy hàm lấy dữ liệu
        results = loop.run_until_complete(run_scraper(start_num, end_num, base_url))
        
        # Tạo bảng kết quả bằng Pandas
        df = pd.DataFrame(results)
        elapsed_time = time.time() - start_time
        
        st.success(f"✅ Đã quét xong trong {elapsed_time:.2f} giây!")
        
        # Hiển thị bảng
        st.dataframe(df, use_container_width=True)
        
        # Nút tải file CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Tải kết quả (CSV)",
            data=csv,
            file_name=f'ket_qua_title_{start_num}_den_{end_num}.csv',
            mime='text/csv',
        )
