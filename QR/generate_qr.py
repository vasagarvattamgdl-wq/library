import qrcode

# Streamlit app URL
url = "https://library-gh68qfhjcinpbcyv8kh898.streamlit.app/"

# Create QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

qr.add_data(url)
qr.make(fit=True)

# Create image
img = qr.make_image(fill_color="black", back_color="white")

# Save to QR folder
img.save("QR/library_qr_code.png")

print("QR code generated successfully!")
print(f"Saved as: QR/library_qr_code.png")
print(f"URL: {url}")
