import streamlit as st
import qrcode
from PIL import Image
from io import BytesIO

st.title("Công cụ tạo mã QR có Logo nội bộ")

# 1. Nhập nội dung
data = st.text_input("Nhập URL hoặc nội dung cần tạo QR:")

# 2. Upload logo
logo_file = st.file_uploader("Tải lên Logo (PNG, JPG)", type=["png", "jpg", "jpeg"])

if data:
    # Bắt buộc dùng ERROR_CORRECT_H (sửa lỗi 30%) để QR vẫn đọc được khi bị logo che
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Tạo ảnh QR và chuyển sang hệ RGB để dán logo màu
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Xử lý chèn logo nếu có
    if logo_file is not None:
        logo = Image.open(logo_file)
        
        # Giới hạn kích thước logo bằng 1/4 kích thước QR code
        logo_size = (qr_img.size[0] // 4, qr_img.size[1] // 4)
        logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
        
        # Tính toán tọa độ để đặt logo vào chính giữa
        pos = ((qr_img.size[0] - logo_size[0]) // 2, (qr_img.size[1] - logo_size[1]) // 2)
        
        # Dán logo vào QR code
        qr_img.paste(logo, pos)
    
    # Xuất file
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    
    st.image(buf, caption="Mã QR của bạn")
    st.download_button(
        label="Tải xuống QR", 
        data=buf.getvalue(), 
        file_name="qrcode_logo.png", 
        mime="image/png"
    )
