#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors=[]
m=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))

def check(cond,msg):
    if not cond:
        errors.append(msg)

check(m.get("schema")==1,"manifest schema must be 1")
check(m.get("channel")=="stable","manifest channel must be stable")

init=(ROOT/"src/t500_flasher/__init__.py").read_text(encoding="utf-8")
mo=re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']',init)
check(bool(mo),"APP_VERSION missing")
if mo:
    check(m["gui"]["version"]==mo.group(1),f"GUI version mismatch manifest={m['gui']['version']} app={mo.group(1)}")

for key in ("windows","linux_x86_64"):
    cfg=m["gui"].get(key,{})
    check(bool(cfg.get("asset")),f"gui.{key}.asset missing")
    check(cfg.get("url","").startswith("https://github.com/Tunglam0605/T500-esp32-firmware-flasher-releases/releases/download/"),f"gui.{key}.url invalid")
    check(m["gui"]["release_tag"] in cfg.get("url",""),f"gui.{key}.url tag mismatch")

expected={
    "ESP32":{"flash_size":"4MB","segments":[("0x1000","bootloader.bin"),("0x8000","partition-table.bin"),("0x10000","espnow_example.bin")],"dir":"classic"},
    "ESP32-S3":{"flash_size":"2MB","segments":[("0x0","bootloader.bin"),("0x8000","partition-table.bin"),("0x10000","t500_s3_legacy.bin")],"dir":"s3"},
}
for chip,e in expected.items():
    cfg=m["firmware"][chip]
    check(cfg["flash_size"]==e["flash_size"],f"{chip} flash_size mismatch")
    check(cfg.get("flash_mode")=="dio",f"{chip} flash_mode must be dio")
    check(cfg.get("flash_freq")=="40m",f"{chip} flash_freq must be 40m")
    segs=cfg["segments"]
    check(len(segs)==3,f"{chip} must have exactly 3 segments")
    for seg,(off,name) in zip(segs,e["segments"]):
        check(seg["offset"].lower()==off.lower(),f"{chip} offset mismatch for {name}")
        check(seg["asset"]==name,f"{chip} asset mismatch expected {name}")
        p=ROOT/"bundled_firmware"/e["dir"]/name
        check(p.is_file(),f"missing {p}")
        if p.is_file():
            got=hashlib.sha256(p.read_bytes()).hexdigest()
            check(got==seg["sha256"],f"{chip} SHA256 mismatch {name}")

for p in [ROOT/"assets/t500_hero.png",ROOT/"assets/logo.png",ROOT/"assets/logo.ico"]:
    check(p.is_file(),f"required asset missing: {p.name}")

if errors:
    print("RELEASE_VALIDATION=FAIL")
    for e in errors:
        print(" -",e)
    sys.exit(1)

print("RELEASE_VALIDATION=PASS")
print("GUI_VERSION",m["gui"]["version"])
print("FIRMWARE ESP32",m["firmware"]["ESP32"]["version"])
print("FIRMWARE ESP32-S3",m["firmware"]["ESP32-S3"]["version"])
