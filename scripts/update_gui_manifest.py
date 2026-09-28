#!/usr/bin/env python3
import json, sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'manifest.json'
if len(sys.argv)!=2: raise SystemExit('usage: update_gui_manifest.py X.Y.Z')
v=sys.argv[1]
m=json.loads(p.read_text())
m['gui']['version']=v
m['gui']['release_tag']=f'gui-v{v}'
m['gui']['windows']['url']=f'https://github.com/Tunglam0605/T500-esp32-firmware-flasher-releases/releases/download/gui-v{v}/T500_Firmware_Flasher_Windows_x64.exe'
m['gui']['linux_x86_64']['url']=f'https://github.com/Tunglam0605/T500-esp32-firmware-flasher-releases/releases/download/gui-v{v}/T500_Firmware_Flasher_Linux_x86_64'
p.write_text(json.dumps(m,indent=2)+'\n')
print('manifest GUI version ->',v)
