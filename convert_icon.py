from PIL import Image
import sys

try:
    img_path = r"C:\Users\goiab\.gemini\antigravity\brain\5fd78100-8c20-4f9e-9936-0c1092fac110\dropout_icon_1775624790893.png"
    img = Image.open(img_path)
    # Resize to have multiple sizes for standard ICO format
    icon_sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    img.save('icon.ico', format='ICO', sizes=icon_sizes)
    print("Icon converted successfully to icon.ico")
except Exception as e:
    print(f"Error converting icon: {e}")
    sys.exit(1)
