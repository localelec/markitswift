"""สร้างไอคอนแอป (app.ico) สำหรับ MarkItSwift — รันครั้งเดียวเพื่อ generate ไฟล์ .ico"""
from PIL import Image, ImageDraw, ImageFont

SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# พื้นหลังโค้งมนไล่เฉดฟ้า
top, bottom = (14, 165, 233), (2, 132, 199)  # sky-500 -> sky-600
for y in range(SIZE):
    t = y / SIZE
    r = int(top[0] + (bottom[0] - top[0]) * t)
    g = int(top[1] + (bottom[1] - top[1]) * t)
    b = int(top[2] + (bottom[2] - top[2]) * t)
    d.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

# ครอบมุมโค้ง
radius = 52
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE, SIZE], radius=radius, fill=255)
img.putalpha(mask)
d = ImageDraw.Draw(img)


def load_font(size):
    for name in ("segoeuib.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ตัว "M" สไตล์โลโก้ markdown
font = load_font(140)
white = (255, 255, 255, 255)
tx, ty = SIZE / 2, SIZE / 2 - 48
d.text((tx, ty), "M", font=font, fill=white, anchor="mm")

# ลูกศรลง ↓ (สัญลักษณ์ markdown = M ตามด้วยลูกศรลง)
ax = SIZE / 2
ay = SIZE - 62
d.line([(ax, ay - 40), (ax, ay + 22)], fill=white, width=20)
d.polygon([(ax - 32, ay + 2), (ax + 32, ay + 2), (ax, ay + 40)], fill=white)

sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save("app.ico", sizes=sizes)
img.save("app.png")
print("สร้าง app.ico และ app.png สำเร็จ")
