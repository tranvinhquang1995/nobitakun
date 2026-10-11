import streamlit as st
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO

st.title("Công cụ tạo mã QR có Logo Hình Tròn")

# 1. Nhập nội dung
data = st.text_input("Nhập URL hoặc nội dung cần tạo QR:")

# 2. Upload logo
logo_file = st.file_uploader("Tải lên Logo (PNG, JPG)", type=["png", "jpg", "jpeg"])

if data:
    # Bắt buộc dùng ERROR_CORRECT_H (sửa lỗi 30%)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Tạo ảnh QR và chuyển sang hệ RGB
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    if logo_file is not None:
        # Mở logo và chuyển sang hệ RGBA để hỗ trợ kênh trong suốt (Alpha)
        logo = Image.open(logo_file).convert("RGBA")
        
        # Cắt logo thành hình vuông (lấy phần trung tâm) để khi bo tròn không bị méo
        min_dim = min(logo.size)
        left = (logo.size[0] - min_dim) / 2
        top = (logo.size[1] - min_dim) / 2
        right = (logo.size[0] + min_dim) / 2
        bottom = (logo.size[1] + min_dim) / 2
        logo = logo.crop((left, top, right, bottom))
        
        # Đổi kích thước logo (bằng 1/4 kích thước QR code)
        logo_size_px = qr_img.size[0] // 4
        logo = logo.resize((logo_size_px, logo_size_px), Image.Resampling.LANCZOS)
        
        # Tạo mặt nạ (mask) hình tròn
        mask = Image.new('L', (logo_size_px, logo_size_px), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, logo_size_px, logo_size_px), fill=255)
        
        # Tính toán tọa độ đặt logo
        pos = ((qr_img.size[0] - logo_size_px) // 2, (qr_img.size[1] - logo_size_px) // 2)
        
        # Dán logo lên QR code, sử dụng mask hình tròn
        qr_img.paste(logo, pos, mask)
    
    # Xuất file
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    
    st.image(buf, caption="Mã QR của bạn")
    st.download_button(
        label="Tải xuống QR", 
        data=buf.getvalue(), 
        file_name="qrcode_round_logo.png", 
        mime="image/png"
    )
