from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
hero = A / "t500_hero.png"
if not hero.exists():
    raise SystemExit("Missing assets/t500_hero.png")

im = Image.open(hero).convert("RGBA")
square = Image.new("RGBA", (1024, 1024), (8, 22, 36, 255))
fit = im.copy()
fit.thumbnail((940, 940), Image.Resampling.LANCZOS)
x = (1024 - fit.width) // 2
y = (1024 - fit.height) // 2
square.alpha_composite(fit, (x, y))
square.save(A / "logo.png", optimize=True)
square.resize((512, 512), Image.Resampling.LANCZOS).save(A / "logo_512.png", optimize=True)
square.resize((256, 256), Image.Resampling.LANCZOS).save(
    A / "logo.ico",
    sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print("generated icons from approved T500 hero artwork")
