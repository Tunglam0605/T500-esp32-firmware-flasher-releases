from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "assets"
A.mkdir(exist_ok=True)

S=1024
im=Image.new("RGBA",(S,S),(6,17,32,255))
# subtle radial-ish layers
bg=Image.new("RGBA",(S,S),(0,0,0,0)); bd=ImageDraw.Draw(bg)
for r,a in [(470,26),(390,24),(310,20)]:
    bd.ellipse((512-r,420-r,512+r,420+r), fill=(0,160,220,a))
bg=bg.filter(ImageFilter.GaussianBlur(80))
im=Image.alpha_composite(im,bg)
d=ImageDraw.Draw(im)

cyan=(21,204,235,255); blue=(32,125,255,255); green=(55,235,155,255)
yellow=(255,205,20,255); silver=(210,220,230,255); dark=(15,28,44,255)

# outer tech ring
d.arc((90,70,934,914), 205, 352, fill=blue, width=24)
d.arc((90,70,934,914), 8, 148, fill=cyan, width=24)
d.arc((105,85,919,899), 20, 70, fill=green, width=18)

# ESP32 chip
chip=(155,190,455,490)
d.rounded_rectangle(chip,40,fill=(10,34,55,255),outline=cyan,width=18)
for x in range(185,440,55):
    d.rectangle((x,160,x+18,192),fill=cyan)
    d.rectangle((x,488,x+18,520),fill=cyan)
for y in range(220,470,55):
    d.rectangle((125,y,158,y+18),fill=cyan)
    d.rectangle((453,y,486,y+18),fill=cyan)
# wifi arcs
for box in [(220,245,390,415),(250,275,360,385),(282,307,328,353)]:
    d.arc(box,205,335,fill=(235,248,255,255),width=18)

# T500 simplified AGV body
# body shadow
d.rounded_rectangle((305,415,785,705),45,fill=(0,0,0,80))
# chassis
d.polygon([(290,430),(660,390),(810,470),(770,690),(345,735),(255,625)],fill=(150,160,170,255))
# top yellow deck
d.polygon([(300,415),(640,382),(760,445),(690,535),(330,570),(250,515)],fill=yellow)
# front bumper
d.polygon([(250,515),(330,570),(330,650),(245,610)],fill=(18,28,40,255))
d.polygon([(330,570),(690,535),(690,625),(330,650)],fill=(35,45,56,255))
# mast
d.rounded_rectangle((575,205,665,440),18,fill=(170,180,190,255),outline=(235,240,245,255),width=5)
d.rounded_rectangle((548,180,692,245),18,fill=(190,200,210,255),outline=(240,245,250,255),width=5)
# side rails
d.rounded_rectangle((520,250,585,405),28,outline=(175,190,200,255),width=18)
d.rounded_rectangle((655,250,720,405),28,outline=(175,190,200,255),width=18)
# stack light
for i,c in enumerate([(235,70,70,255),(250,200,30,255),(55,205,95,255)]):
    d.rectangle((608,126+i*25,632,150+i*25),fill=c)
d.rounded_rectangle((605,116,635,205),12,outline=silver,width=4)
# buttons
for cy,c in [(273,(40,210,90,255)),(306,(225,55,55,255)),(344,(255,150,25,255))]:
    d.ellipse((611,cy,628,cy+17),fill=c)
# hazard side
for x in (278,728):
    d.rectangle((x,455,x+46,560),fill=yellow)
    for yy in (455,500):
        d.polygon([(x,yy),(x+18,yy),(x+46,yy+32),(x+46,yy+50)],fill=(25,25,25,255))

# lightning bolt
d.polygon([(780,205),(690,365),(755,365),(705,495),(870,285),(790,285)],fill=green)

# upload icon
d.arc((745,410,895,560),35,320,fill=cyan,width=16)
d.polygon([(820,438),(780,488),(806,488),(806,526),(834,526),(834,488),(860,488)],fill=cyan)

# text
try:
    f_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",150)
    f_mid=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",66)
except Exception:
    f_big=f_mid=ImageFont.load_default()
# T500
text="T500"; box=d.textbbox((0,0),text,font=f_big); tw=box[2]-box[0]
d.text(((S-tw)//2,700),text,font=f_big,fill=(238,244,250,255),stroke_width=2,stroke_fill=(70,90,110,255))
# subtitle
sub="ESP32 FLASHER"; box=d.textbbox((0,0),sub,font=f_mid); sw=box[2]-box[0]
d.text(((S-sw)//2,855),sub,font=f_mid,fill=cyan)

# small yellow accent
d.rounded_rectangle((452,946,572,958),6,fill=yellow)

im.save(A/"logo.png",optimize=True)
im.resize((512,512),Image.Resampling.LANCZOS).save(A/"logo_512.png",optimize=True)
im.resize((256,256),Image.Resampling.LANCZOS).save(A/"logo.ico",sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("generated",A/"logo.png")
