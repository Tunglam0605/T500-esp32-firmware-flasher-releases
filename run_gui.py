import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "--self-test" in sys.argv:
    from t500_flasher import APP_VERSION
    from t500_flasher import core
    manifest = core.read_bundled_manifest()
    print(f"T500 Firmware Flasher v{APP_VERSION}")
    print("schema", manifest.get("schema"))
    for chip in ("ESP32", "ESP32-S3"):
        cfg, segments = core.resolve_firmware(chip, manifest)
        print(chip, cfg["version"], cfg["release_tag"])
        for offset, path in segments:
            print("PASS", chip, offset, path.name, core.sha256_file(path))
    print("SELF_TEST=PASS")
    raise SystemExit(0)

from t500_flasher.app import main
main()
