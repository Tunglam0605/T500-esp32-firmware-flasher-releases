from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
hero = A / "t500_hero.png"
if not hero.exists():
    raise SystemExit("Missing assets/t500_hero.png")

im = Image.open(hero).convert("RGBA")

# App icon: vehicle-only crop from approved banner. Deliberately excludes T500/ESP32 FLASHER text.
# The approved artwork is 3:1-ish, with the vehicle on the left side.
w, h = im.size
crop = im.crop((0, 0, min(int(h * 1.30), w), h))

# Fit to square with a matching dark-navy background so the AGV remains readable at 16-64 px.
square = Image.new("RGBA", (1024, 1024), (7, 26, 48, 255))
crop.thumbnail((930, 930), Image.Resampling.LANCZOS)
x = (1024 - crop.width) // 2
y = (1024 - crop.height) // 2
square.alpha_composite(crop, (x, y))

square.save(A / "logo_app.png", optimize=True)
square.resize((512, 512), Image.Resampling.LANCZOS).save(A / "logo_app_512.png", optimize=True)
square.resize((256, 256), Image.Resampling.LANCZOS).save(
    A / "logo_app.ico",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)

# Compatibility names used by older packaging scripts.
square.save(A / "logo.png", optimize=True)
square.resize((512, 512), Image.Resampling.LANCZOS).save(A / "logo_512.png", optimize=True)
square.resize((256, 256), Image.Resampling.LANCZOS).save(
    A / "logo.ico",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print("APP_ICON=vehicle-only")
print("HERO_BANNER=unchanged")
