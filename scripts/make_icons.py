from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'
A.mkdir(exist_ok=True)
size = 1024
im = Image.new('RGBA', (size, size), '#101820')
d = ImageDraw.Draw(im)
d.rounded_rectangle((120,120,904,904), radius=190, fill='#101820', outline='#19A7C7', width=34)
for x in (250,380,512,644,774):
    d.line((x,75,x,150), fill='#1FB6D5', width=26)
    d.line((x,874,x,949), fill='#43A047', width=26)
for y in (250,380,512,644,774):
    d.line((75,y,150,y), fill='#1FB6D5', width=26)
    d.line((874,y,949,y), fill='#43A047', width=26)
bolt=[(575,245),(355,545),(500,545),(445,760),(680,420),(530,420)]
d.polygon(bolt, fill='#21B7C9')
try:
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',78)
except Exception:
    font=ImageFont.load_default()
text='T500'
box=d.textbbox((0,0),text,font=font)
d.text(((size-(box[2]-box[0]))/2,815),text,font=font,fill='#EEF7FF')
im.save(A/'logo.png')
im.resize((256,256), Image.Resampling.LANCZOS).save(A/'logo.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(A/'logo.png')
print(A/'logo.ico')
