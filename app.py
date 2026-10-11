import streamlit as st
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO

st.title("Công cụ tạo mã QR có Logo Tròn & Viền Trắng")

# 1. Nhập nội dung
data = st.text_input("Nhập URL hoặc nội dung cần tạo QR:")

# 2. Upload logo
logo_file = st.file_uploader("Tải lên Logo (PNG, JPG)", type=["png", "jpg", "jpeg"])

# 3. Thanh trượt chỉnh độ dày viền trắng
border_thickness = st.slider("Độ dày viền trắng (pixel):", min_value=0, max_value=30, value=15)

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
        logo = Image.open(logo_file).convert("RGBA")
        
        # Cắt logo thành hình vuông
        min_dim = min(logo.size)
        left = (logo.size[0] - min_dim) // 2
        top = (logo.size[1] - min_dim) // 2
        right = (logo.size[0] + min_dim) // 2
        bottom = (logo.size[1] + min_dim) // 2
        logo = logo.crop((left, top, right, bottom))
        
        # Kích thước tổng của cụm Logo + Viền trắng (Bằng 1/4 QR)
        outer_size_px = qr_img.size[0] // 4
        
        # Kích thước thực tế của Logo bên trong (đã trừ đi viền 2 bên)
        inner_size_px = outer_size_px - (border_thickness * 2)
        
        if inner_size_px > 0:
            # Thu phóng logo theo kích thước bên trong
            logo = logo.resize((inner_size_px, inner_size_px), Image.Resampling.LANCZOS)
            
            # Tạo mask hình tròn cho logo (inner)
            inner_mask = Image.new('L', (inner_size_px, inner_size_px), 0)
            draw_inner = ImageDraw.Draw(inner_mask)
            draw_inner.ellipse((0, 0, inner_size_px, inner_size_px), fill=255)
            
            # Tạo mask hình tròn cho viền trắng ngoài (outer)
            outer_mask = Image.new('L', (outer_size_px, outer_size_px), 0)
            draw_outer = ImageDraw.Draw(outer_mask)
            draw_outer.ellipse((0, 0, outer_size_px, outer_size_px), fill=255)
            
            # Tạo một hình nền màu trắng (vuông)
            white_bg = Image.new('RGB', (outer_size_px, outer_size_px), (255, 255, 255))
            
            # Dán logo vào chính giữa nền trắng bằng inner_mask
            white_bg.paste(logo, (border_thickness, border_thickness), inner_mask)
            
            # Tính toán tọa độ đặt cụm logo lên QR
            pos = ((qr_img.size[0] - outer_size_px) // 2, (qr_img.size[1] - outer_size_px) // 2)
            
            # Dán cụm nền trắng (đã có logo) lên QR bằng outer_mask để cắt bo tròn toàn bộ
            qr_img.paste(white_bg, pos, outer_mask)
