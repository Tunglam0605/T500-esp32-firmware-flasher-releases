from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
A.mkdir(exist_ok=True)

S = 1024
im = Image.new("RGBA", (S, S), (248, 250, 252, 255))
d = ImageDraw.Draw(im)

ink = (38, 47, 56, 255)
mid = (184, 191, 199, 255)
body = (204, 210, 216, 255)
yellow = (244, 195, 0, 255)
cyan = (20, 125, 146, 255)
dark = (58, 68, 78, 255)

# soft badge ring
d.rounded_rectangle((56, 56, 968, 968), 180, fill=(255,255,255,255), outline=(221,226,232,255), width=16)

# Real-T500-inspired restrained silhouette: low chassis, sloped yellow deck, rear mast.
# chassis
d.polygon([(180,550),(245,455),(650,435),(790,500),(760,645),(270,670),(160,615)], fill=body)
d.line([(180,550),(245,455),(650,435),(790,500),(760,645),(270,670),(160,615),(180,550)], fill=ink, width=18, joint="curve")

# yellow sloped upper deck
d.polygon([(240,462),(620,442),(728,486),(646,540),(235,566),(170,530)], fill=yellow)
d.line([(240,462),(620,442),(728,486),(646,540),(235,566),(170,530)], fill=ink, width=14, joint="curve")

# dark lower side
d.polygon([(235,568),(646,542),(759,504),(754,628),(272,653),(168,610),(168,536)], fill=dark)
d.line([(235,568),(646,542),(759,504)], fill=ink, width=12)

# rear mast
d.rounded_rectangle((566,250,654,447), radius=16, fill=mid, outline=ink, width=14)
d.rounded_rectangle((535,216,690,272), radius=16, fill=(218,223,228,255), outline=ink, width=12)

# side safety rails
d.arc((490,288,592,462), start=100, end=260, fill=(126,137,148,255), width=18)
d.arc((645,286,748,465), start=-80, end=80, fill=(126,137,148,255), width=18)

# stack light
for y,c in [(168,(220,64,52,255)),(191,(238,173,27,255)),(214,(55,170,83,255))]:
    d.rectangle((603,y,623,y+20), fill=c)
d.rounded_rectangle((596,160,630,240), radius=8, outline=ink, width=5)

# wheels
for cx,cy in [(286,654),(666,635)]:
    d.ellipse((cx-28,cy-28,cx+28,cy+28), fill=(30,35,40,255), outline=ink, width=5)

# small controller-chip motif, not fantasy vehicle geometry
d.rounded_rectangle((160,730,350,855), radius=22, fill=(238,243,247,255), outline=cyan, width=12)
for x in range(182,334,38):
    d.rectangle((x,712,x+12,733), fill=cyan)
    d.rectangle((x,852,x+12,873), fill=cyan)
for y in range(750,838,32):
    d.rectangle((140,y,162,y+12), fill=cyan)
    d.rectangle((348,y,370,y+12), fill=cyan)
d.arc((205,760,315,840), start=200, end=340, fill=cyan, width=12)
d.arc((225,780,295,830), start=200, end=340, fill=cyan, width=10)

# simple flash arrow
d.line((430,790,690,790), fill=cyan, width=20)
d.polygon([(690,790),(635,752),(635,828)], fill=cyan)

# T500 bar
d.rounded_rectangle((170,900,854,928), radius=14, fill=yellow)

im.save(A / "logo.png", optimize=True)
im.resize((512,512), Image.Resampling.LANCZOS).save(A / "logo_512.png", optimize=True)
im.resize((256,256), Image.Resampling.LANCZOS).save(A / "logo.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("generated accurate T500 branding assets")
