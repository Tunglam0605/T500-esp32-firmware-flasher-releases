from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
hero = A / "t500_hero.png"
if not hero.exists():
    raise SystemExit("Missing assets/t500_hero.png")

im = Image.open(hero).convert("RGBA")
w, h = im.size

# App icon = vehicle area only. Crop tightly around the left-side T500 vehicle and mast,
# excluding the T500/ESP32 FLASHER wordmark on the right.
left = int(w * 0.035)
top = int(h * 0.025)
right = int(w * 0.47)
bottom = int(h * 0.96)
vehicle = im.crop((left, top, right, bottom))

# Make the vehicle fill the icon; very little empty margin so it stays readable at 16-48 px.
square = Image.new("RGBA", (1024, 1024), (7, 26, 48, 255))
vehicle.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
x = (1024 - vehicle.width) // 2
y = (1024 - vehicle.height) // 2
square.alpha_composite(vehicle, (x, y))

for name, size in [("logo_app.png",1024), ("logo_app_512.png",512), ("logo.png",1024), ("logo_512.png",512)]:
    out = square if size == 1024 else square.resize((size,size), Image.Resampling.LANCZOS)
    out.save(A / name, optimize=True)

ico = square.resize((256,256), Image.Resampling.LANCZOS)
for name in ("logo_app.ico","logo.ico"):
    ico.save(A / name, sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])

print("APP_ICON=vehicle-only-tight-crop")
print("HERO_BANNER=unchanged")
