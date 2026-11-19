import streamlit as st
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO

st.set_page_config(page_title="Tạo QR Code", page_icon="🔳")

st.title("Công cụ tạo mã QR có Logo Tròn & Viền Trắng")

# 1. Nhập liệu
data = st.text_input("Nhập URL hoặc nội dung cần tạo QR:")
logo_file = st.file_uploader("Tải lên Logo (PNG, JPG)", type=["png", "jpg", "jpeg"])
border_thickness = st.slider("Độ dày viền trắng (pixel):", min_value=0, max_value=60, value=20)

if data:
    # 2. Tạo mã QR cơ bản với box_size=30 để tăng chất lượng ảnh (độ phân giải cao)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=30,  # <-- ĐÃ TĂNG TỪ 10 LÊN 30
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Chuyển thành ảnh RGB
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # 3. Xử lý Logo nếu có upload
    if logo_file is not None:
        logo = Image.open(logo_file).convert("RGBA")
        
        # Cắt logo thành hình vuông (lấy phần tâm)
        min_dim = min(logo.size)
        left = (logo.size[0] - min_dim) // 2
        top = (logo.size[1] - min_dim) // 2
        right = (logo.size[0] + min_dim) // 2
        bottom = (logo.size[1] + min_dim) // 2
        logo = logo.crop((left, top, right, bottom))
        
        # Tính toán kích thước
        outer_size_px = qr_img.size[0] // 4
        inner_size_px = outer_size_px - (border_thickness * 2)
        
        if inner_size_px > 0:
            # Thu phóng logo
            logo = logo.resize((inner_size_px, inner_size_px), Image.Resampling.LANCZOS)
            
            # Tạo mask tròn cho logo
            inner_mask = Image.new('L', (inner_size_px, inner_size_px), 0)
            draw_inner = ImageDraw.Draw(inner_mask)
            draw_inner.ellipse((0, 0, inner_size_px, inner_size_px), fill=255)
            
            # Tạo mask tròn cho viền ngoài
            outer_mask = Image.new('L', (outer_size_px, outer_size_px), 0)
            draw_outer = ImageDraw.Draw(outer_mask)
            draw_outer.ellipse((0, 0, outer_size_px, outer_size_px), fill=255)
            
            # Tạo phông nền trắng vuông cho viền
            white_bg = Image.new('RGB', (outer_size_px, outer_size_px), (255, 255, 255))
            
            # Dán logo vào phông trắng (cắt tròn logo)
            white_bg.paste(logo, (border_thickness, border_thickness), inner_mask)
            
            # Tính toán vị trí trung tâm của QR
            pos = ((qr_img.size[0] - outer_size_px) // 2, (qr_img.size[1] - outer_size_px) // 2)
            
            # Dán toàn bộ cụm (Logo + Nền trắng) lên QR
            qr_img.paste(white_bg, pos, outer_mask)
        else:
            st.warning("⚠️ Độ dày viền quá lớn che mất logo! Mã QR xuất ra sẽ không có logo.")
    
    # 4. Xuất File
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    
    st.image(buf, caption=f"Mã QR của bạn (Kích thước: {qr_img.size[0]}x{qr_img.size[1]}px)")
    st.download_button(
        label="📥 Tải xuống QR chất lượng cao", 
        data=buf.getvalue(), 
        file_name="qrcode_high_res.png", 
        mime="image/png"
    )
else:
    st.info("👉 Vui lòng nhập URL hoặc nội dung để mã QR xuất hiện.")
