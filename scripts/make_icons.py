from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
vehicle_raw = A / "t500_vehicle_raw.jpg"
if not vehicle_raw.exists():
    raise SystemExit("Missing assets/t500_vehicle_raw.jpg")

im = Image.open(vehicle_raw).convert("RGBA")
w, h = im.size

# Transparent background outside the squircle
square = Image.new("RGBA", (w, h), (0, 0, 0, 0))
for y in range(h):
    for x in range(w):
        r, g, b, _ = im.getpixel((x, y))
        # Outer corner mask
        if r < 8 and g < 8 and b < 8 and ((x < 240 or x > w - 240) and (y < 240 or y > h - 240)):
            square.putpixel((x, y), (0, 0, 0, 0))
        else:
            square.putpixel((x, y), (r, g, b, 255))

for name, size in [("logo_app.png", 1024), ("logo_app_512.png", 512), ("logo.png", 1024), ("logo_512.png", 512)]:
    out = square if size == 1024 else square.resize((size, size), Image.Resampling.LANCZOS)
    out.save(A / name, optimize=True)

ico = square.resize((256, 256), Image.Resampling.LANCZOS)
for name in ("logo_app.ico", "logo.ico"):
    ico.save(A / name, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print("APP_ICON=vehicle-only-source-asset")
print("HERO_BANNER=assets/t500_hero.png")
