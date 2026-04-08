import os
from PIL import Image

def recolor(img, mode):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    
    for r, g, b, a in data:
        if a == 0:
            new_data.append((0, 0, 0, 0))
            continue
            
        if mode == "desert":
            lum = (r * 0.3 + g * 0.59 + b * 0.11)
            nr = int(min(255, lum * 1.5))
            ng = int(min(255, lum * 1.1))
            nb = int(min(255, lum * 0.5))
            new_data.append((nr, ng, nb, a))
            
        elif mode == "snow":
            lum = (r * 0.3 + g * 0.59 + b * 0.11)
            nr = int(min(255, lum * 0.8 + 50))
            ng = int(min(255, lum * 0.9 + 50))
            nb = int(min(255, lum * 1.2 + 80))
            new_data.append((nr, ng, nb, a))
            
    img.putdata(new_data)
    return img

base_dir = "assets/backgrounds/florest"
ds_dir = "assets/backgrounds/desert" 
sn_dir = "assets/backgrounds/snow"

os.makedirs(ds_dir, exist_ok=True)
os.makedirs(sn_dir, exist_ok=True)

files = [f for f in os.listdir(base_dir) if f.endswith(".png")]

for f in files:
    path = os.path.join(base_dir, f)
    img = Image.open(path)
    
    d_img = recolor(img, "desert")
    d_img.save(os.path.join(ds_dir, f))
    
    s_img = recolor(img, "snow")
    s_img.save(os.path.join(sn_dir, f))
    
print("FINISH")
