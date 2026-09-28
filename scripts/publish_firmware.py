#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'manifest.json'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def main():
    if len(sys.argv)!=6:
        raise SystemExit('usage: publish_firmware.py <classic|s3> <version> <bootloader.bin> <partition-table.bin> <app.bin>')
    family, version = sys.argv[1], sys.argv[2]
    boot, part, app = map(Path, sys.argv[3:6])
    if family not in ('classic','s3'): raise SystemExit('family must be classic or s3')
    for p in (boot,part,app):
        if not p.is_file(): raise SystemExit(f'missing {p}')
    chip='ESP32' if family=='classic' else 'ESP32-S3'
    tag=f'fw-{family}-v{version}'
    app_name='espnow_example.bin' if family=='classic' else 't500_s3_legacy.bin'
    stage=ROOT/'.release-staging'/tag
    shutil.rmtree(stage,ignore_errors=True); stage.mkdir(parents=True)
    shutil.copy2(boot,stage/'bootloader.bin')
    shutil.copy2(part,stage/'partition-table.bin')
    shutil.copy2(app,stage/app_name)
    m=json.loads(MANIFEST.read_text())
    cfg=m['firmware'][chip]
    cfg['version']=version; cfg['release_tag']=tag
    names=['bootloader.bin','partition-table.bin',app_name]
    for seg,name in zip(cfg['segments'],names):
        seg['asset']=name; seg['sha256']=sha(stage/name)
    MANIFEST.write_text(json.dumps(m,indent=2)+'\n')
    subprocess.run(['gh','release','create',tag,str(stage/'bootloader.bin'),str(stage/'partition-table.bin'),str(stage/app_name),'--repo','Tunglam0605/T500-esp32-firmware-flasher-releases','--title',f'{chip} firmware v{version}','--notes',f'Flash-ready {chip} firmware artifacts for T500 Firmware Flasher.'],check=True)
    print(f'Created {tag}')
    print('manifest.json updated. Review, commit and push it.')
if __name__=='__main__': main()
