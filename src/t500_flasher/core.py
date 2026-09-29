from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import esptool
from packaging.version import Version
from serial.tools import list_ports

OWNER = "Tunglam0605"
REPO = "T500-esp32-firmware-flasher-releases"
RAW_MANIFEST = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/main/manifest.json"
RELEASE_BASE = f"https://github.com/{OWNER}/{REPO}/releases/download"

BUNDLED_VERSION = {"ESP32": "1.0.0", "ESP32-S3": "1.0.0"}

def bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))

def data_root() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        return root / "T500FirmwareFlasher"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "T500FirmwareFlasher"

def cache_root() -> Path:
    p = data_root() / "firmware"
    p.mkdir(parents=True, exist_ok=True)
    return p

def read_bundled_manifest() -> dict:
    return json.loads((bundle_root() / "manifest.json").read_text(encoding="utf-8"))

def fetch_manifest(timeout: int = 8) -> dict:
    req = urllib.request.Request(RAW_MANIFEST, headers={"User-Agent": "T500-Firmware-Flasher"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def list_serial_ports() -> list[tuple[str, str]]:
    result = []
    for p in list_ports.comports():
        label = p.device
        details = " ".join(x for x in [p.manufacturer, p.description] if x)
        result.append((label, details))
    return result

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def run_esptool(args: list[str], progress=None) -> tuple[bool, str]:
    class ProgressBuffer(io.StringIO):
        def __init__(self, callback=None):
            super().__init__()
            self.callback = callback
            self._last_percent = -1

        def write(self, text):
            n = super().write(text)
            if self.callback and text:
                for match in re.finditer(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)%", text):
                    try:
                        pct = max(0, min(100, int(float(match.group(1)))))
                        if pct != self._last_percent:
                            self._last_percent = pct
                            self.callback(pct)
                    except Exception:
                        pass
            return n

    out = ProgressBuffer(progress)
    try:
        with redirect_stdout(out), redirect_stderr(out):
            try:
                esptool.main(args)
            except SystemExit as e:
                if e.code not in (0, None):
                    raise RuntimeError(f"esptool exit {e.code}")
        return True, out.getvalue()
    except Exception as e:
        return False, out.getvalue() + "\n" + repr(e)

def detect_chip(port: str) -> tuple[str | None, str, str]:
    ok, output = run_esptool(["--port", port, "chip-id"])
    if not ok:
        return None, "-", output
    chip = None
    if re.search(r"ESP32-S3", output, re.I):
        chip = "ESP32-S3"
    elif re.search(r"\bESP32\b", output, re.I):
        chip = "ESP32"
    m = re.search(r"MAC:\s*([0-9A-Fa-f:]{17})", output)
    mac = m.group(1).upper() if m else "-"
    return chip, mac, output

def release_url(tag: str, asset: str) -> str:
    return f"{RELEASE_BASE}/{tag}/{asset}"

def cached_meta_path(chip: str) -> Path:
    return cache_root() / chip.replace("-", "_") / "metadata.json"

def installed_firmware_version(chip: str) -> str:
    meta = cached_meta_path(chip)
    if meta.exists():
        try:
            return json.loads(meta.read_text(encoding="utf-8")).get("version", BUNDLED_VERSION[chip])
        except Exception:
            pass
    return BUNDLED_VERSION[chip]

def firmware_needs_update(chip: str, manifest: dict) -> bool:
    remote = manifest["firmware"][chip]["version"]
    return Version(remote) > Version(installed_firmware_version(chip))

def _bundled_segment_path(chip: str, asset: str) -> Path:
    sub = "classic" if chip == "ESP32" else "s3"
    return bundle_root() / "bundled_firmware" / sub / asset

def resolve_firmware(chip: str, manifest: dict) -> tuple[dict, list[tuple[str, Path]]]:
    cfg = manifest["firmware"][chip]
    cached_dir = cache_root() / chip.replace("-", "_") / cfg["version"]
    cached = []
    all_cached = True
    for seg in cfg["segments"]:
        p = cached_dir / seg["asset"]
        if not p.exists() or sha256_file(p) != seg["sha256"]:
            all_cached = False
            break
        cached.append((seg["offset"], p))
    if all_cached:
        return cfg, cached

    # Offline fallback is the immutable validated baseline bundled into the GUI.
    if cfg["version"] == BUNDLED_VERSION[chip]:
        bundled = []
        for seg in cfg["segments"]:
            p = _bundled_segment_path(chip, seg["asset"])
            if not p.exists() or sha256_file(p) != seg["sha256"]:
                raise RuntimeError(f"Bundled firmware hash mismatch: {seg['asset']}")
            bundled.append((seg["offset"], p))
        return cfg, bundled

    raise RuntimeError("Firmware mới chưa được tải về. Hãy bấm Đồng bộ firmware trước.")

def sync_firmware(chip: str, manifest: dict, progress=None) -> Path:
    cfg = manifest["firmware"][chip]
    target = cache_root() / chip.replace("-", "_") / cfg["version"]
    target.mkdir(parents=True, exist_ok=True)

    total = len(cfg["segments"])
    for idx, seg in enumerate(cfg["segments"], start=1):
        dest = target / seg["asset"]
        if dest.exists() and sha256_file(dest) == seg["sha256"]:
            if progress:
                progress(idx, total, f"Đã có {seg['asset']}")
            continue
        url = release_url(cfg["release_tag"], seg["asset"])
        tmp = dest.with_suffix(dest.suffix + ".part")
        req = urllib.request.Request(url, headers={"User-Agent": "T500-Firmware-Flasher"})
        with urllib.request.urlopen(req, timeout=30) as r, tmp.open("wb") as f:
            shutil.copyfileobj(r, f)
        got = sha256_file(tmp)
        if got != seg["sha256"]:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"SHA256 FAIL {seg['asset']}\nExpected {seg['sha256']}\nGot {got}")
        tmp.replace(dest)
        if progress:
            progress(idx, total, f"Đã tải {seg['asset']}")

    meta = {
        "chip": chip,
        "version": cfg["version"],
        "release_tag": cfg["release_tag"],
        "installed_at": int(time.time()),
    }
    cached_meta_path(chip).parent.mkdir(parents=True, exist_ok=True)
    cached_meta_path(chip).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return target

def flash_firmware(port: str, chip: str, manifest: dict, progress=None) -> tuple[bool, str]:
    cfg, segments = resolve_firmware(chip, manifest)
    chip_arg = "esp32s3" if chip == "ESP32-S3" else "esp32"
    args = [
        "--chip", chip_arg,
        "--port", port,
        "--baud", "460800",
        "--before", "default-reset",
        "--after", "hard-reset",
        "write-flash",
        "--flash-mode", cfg.get("flash_mode", "dio"),
        "--flash-freq", cfg.get("flash_freq", "40m"),
        "--flash-size", cfg["flash_size"],
    ]
    for offset, path in segments:
        args += [offset, str(path)]
    return run_esptool(args, progress=progress)

def platform_manifest_key() -> str:
    if os.name == "nt":
        return "windows"
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "linux_x86_64"
    raise RuntimeError(f"Unsupported GUI update platform: {platform.system()} {machine}")

def gui_update_available(current_version: str, manifest: dict) -> bool:
    return Version(manifest["gui"]["version"]) > Version(current_version)

def download_gui_update(manifest: dict, progress=None) -> Path:
    key = platform_manifest_key()
    cfg = manifest["gui"][key]
    url = cfg["url"]
    suffix = ".exe" if os.name == "nt" else ""
    dest = Path(tempfile.gettempdir()) / f"T500_Firmware_Flasher_{manifest['gui']['version']}{suffix}"
    req = urllib.request.Request(url, headers={"User-Agent": "T500-Firmware-Flasher"})
    with urllib.request.urlopen(req, timeout=60) as r, dest.open("wb") as f:
        length = int(r.headers.get("Content-Length", "0"))
        read = 0
        while True:
            b = r.read(1024 * 1024)
            if not b:
                break
            f.write(b)
            read += len(b)
            if progress:
                progress(read, length)
    expected = cfg.get("sha256")
    if expected and sha256_file(dest) != expected:
        dest.unlink(missing_ok=True)
        raise RuntimeError("GUI update SHA256 mismatch")
    if os.name != "nt":
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest

def schedule_self_replace(downloaded: Path):
    current = Path(sys.executable).resolve()
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Self-update chỉ hoạt động trên bản executable đã đóng gói.")

    if os.name == "nt":
        script = Path(tempfile.gettempdir()) / "t500_update.cmd"
        script.write_text(
            '@echo off\r\n'
            'timeout /t 2 /nobreak >nul\r\n'
            f'copy /Y "{downloaded}" "{current}" >nul\r\n'
            f'start "" "{current}"\r\n'
            'del "%~f0"\r\n',
            encoding="utf-8",
        )
        subprocess.Popen(["cmd", "/c", str(script)], creationflags=0x08000000)
    else:
        script = Path(tempfile.gettempdir()) / "t500_update.sh"
        script.write_text(
            "#!/usr/bin/env bash\n"
            "sleep 2\n"
            f'cp "{downloaded}" "{current}"\n'
            f'chmod +x "{current}"\n'
            f'exec "{current}"\n',
            encoding="utf-8",
        )
        script.chmod(0o755)
        subprocess.Popen(["/bin/bash", str(script)], start_new_session=True)
