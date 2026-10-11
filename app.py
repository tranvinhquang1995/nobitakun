import streamlit as st
import qrcode
from io import BytesIO

st.title("Công cụ tạo mã QR nội bộ")
data = st.text_input("Nhập URL hoặc nội dung cần tạo QR:")

if data:
    # Cấu hình mã QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    
    # Tạo hình ảnh
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Lưu vào buffer để hiển thị và tải xuống
    buf = BytesIO()
    img.save(buf, format="PNG")
    
    st.image(buf, caption="Mã QR của bạn")
    st.download_button(
        label="Tải xuống QR", 
        data=buf.getvalue(), 
        file_name="qrcode.png", 
        mime="image/png"
    )
