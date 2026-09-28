from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QPlainTextEdit, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget
)

from . import APP_VERSION
from . import core

QSS = """
QWidget { background:#0B1220; color:#E8EEF7; font-family:'Segoe UI','Ubuntu'; font-size:13px; }
QMainWindow { background:#0B1220; }
QFrame#card { background:#111C2E; border:1px solid #223451; border-radius:16px; }
QLabel#title { font-size:26px; font-weight:700; color:#F6FAFF; }
QLabel#subtitle { color:#91A4BD; }
QLabel#metric { color:#8EA3BD; }
QLabel#value { font-size:14px; font-weight:650; color:#F3F8FF; }
QLabel#badge { background:#13243B; border:1px solid #284566; border-radius:10px; padding:5px 10px; color:#7DD3FC; }
QComboBox { background:#0E1828; border:1px solid #2A405F; border-radius:9px; padding:8px 10px; }
QComboBox QAbstractItemView { background:#111C2E; selection-background-color:#1B78C5; }
QPushButton { background:#18273B; border:1px solid #304B6D; border-radius:10px; padding:9px 14px; font-weight:600; }
QPushButton:hover { background:#203552; border-color:#3D6C9C; }
QPushButton:disabled { color:#53647B; background:#111A28; border-color:#1B2B40; }
QPushButton#primary { background:#087EA4; border-color:#1FB6D5; color:white; }
QPushButton#primary:hover { background:#0A91B9; }
QPushButton#success { background:#167A4A; border-color:#35C17A; color:white; }
QPushButton#update { background:#6741D9; border-color:#8B6DF0; color:white; }
QPlainTextEdit { background:#08111E; border:1px solid #223451; border-radius:12px; padding:8px; color:#BFD3EA; font-family:'JetBrains Mono','Consolas','Monospace'; }
QProgressBar { background:#0E1828; border:1px solid #263C59; border-radius:7px; height:12px; text-align:center; }
QProgressBar::chunk { background:#16A6C9; border-radius:6px; }
"""

class Signals(QObject):
    done = Signal(object)
    error = Signal(str)
    log = Signal(str)
    progress = Signal(int, int, str)

class Job(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = Signals()

    @Slot()
    def run(self):
        try:
            self.signals.done.emit(self.fn(self.signals))
        except Exception:
            self.signals.error.emit(traceback.format_exc())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self.remote_manifest = core.read_bundled_manifest()
        self.detected_chip = None
        self.detected_mac = "-"
        self.setWindowTitle(f"T500 Firmware Flasher v{APP_VERSION}")
        self.setMinimumSize(980, 720)
        self.setStyleSheet(QSS)

        logo_path = core.bundle_root() / "assets/logo.svg"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        if logo_path.exists():
            logo = QSvgWidget(str(logo_path))
            logo.setFixedSize(72, 72)
            header.addWidget(logo)
        text = QVBoxLayout()
        title = QLabel("T500 Firmware Flasher")
        title.setObjectName("title")
        subtitle = QLabel("ESP32 / ESP32-S3 • Auto detect • Verified firmware • GitHub update channel")
        subtitle.setObjectName("subtitle")
        text.addWidget(title)
        text.addWidget(subtitle)
        header.addLayout(text, 1)
        self.gui_badge = QLabel(f"GUI v{APP_VERSION}")
        self.gui_badge.setObjectName("badge")
        header.addWidget(self.gui_badge, 0, Qt.AlignTop)
        layout.addLayout(header)

        top_card = QFrame(); top_card.setObjectName("card")
        top = QVBoxLayout(top_card); top.setContentsMargins(16,16,16,16); top.setSpacing(12)
        row = QHBoxLayout()
        self.port = QComboBox()
        self.port.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row.addWidget(QLabel("Cổng serial"))
        row.addWidget(self.port, 1)
        self.scan_btn = QPushButton("Quét cổng")
        self.detect_btn = QPushButton("Nhận diện chip")
        self.detect_btn.setObjectName("primary")
        row.addWidget(self.scan_btn); row.addWidget(self.detect_btn)
        top.addLayout(row)

        metrics = QHBoxLayout()
        self.chip_value = self.add_metric(metrics, "CHIP", "Chưa nhận diện")
        self.mac_value = self.add_metric(metrics, "MAC", "-")
        self.fw_local_value = self.add_metric(metrics, "FW LOCAL", "-")
        self.fw_latest_value = self.add_metric(metrics, "FW MỚI NHẤT", "-")
        top.addLayout(metrics)
        layout.addWidget(top_card)

        update_card = QFrame(); update_card.setObjectName("card")
        updates = QHBoxLayout(update_card); updates.setContentsMargins(16,14,16,14)
        self.update_status = QLabel("Kênh stable • chưa kiểm tra cập nhật")
        self.update_status.setObjectName("subtitle")
        updates.addWidget(self.update_status, 1)
        self.check_btn = QPushButton("Kiểm tra cập nhật")
        self.sync_btn = QPushButton("Đồng bộ firmware")
        self.gui_update_btn = QPushButton("Cập nhật ứng dụng")
        self.gui_update_btn.setObjectName("update")
        self.sync_btn.setEnabled(False)
        self.gui_update_btn.setEnabled(False)
        updates.addWidget(self.check_btn); updates.addWidget(self.sync_btn); updates.addWidget(self.gui_update_btn)
        layout.addWidget(update_card)

        action_card = QFrame(); action_card.setObjectName("card")
        act = QVBoxLayout(action_card); act.setContentsMargins(16,16,16,16)
        action_row = QHBoxLayout()
        self.flash_btn = QPushButton("⚡  NẠP FIRMWARE")
        self.flash_btn.setObjectName("success")
        self.flash_btn.setMinimumHeight(46)
        self.flash_btn.setEnabled(False)
        action_row.addWidget(self.flash_btn, 1)
        self.state_label = QLabel("SẴN SÀNG")
        self.state_label.setObjectName("badge")
        action_row.addWidget(self.state_label)
        act.addLayout(action_row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        act.addWidget(self.progress)
        layout.addWidget(action_card)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Log kỹ thuật...")
        layout.addWidget(self.log, 1)

        self.scan_btn.clicked.connect(self.refresh_ports)
        self.detect_btn.clicked.connect(self.detect)
        self.check_btn.clicked.connect(self.check_updates)
        self.sync_btn.clicked.connect(self.sync_firmware)
        self.gui_update_btn.clicked.connect(self.update_gui)
        self.flash_btn.clicked.connect(self.flash)

        self.refresh_ports()
        self.append_log(f"T500 Firmware Flasher v{APP_VERSION} started.")
        self.check_updates(silent=True)

    def add_metric(self, parent, name, initial):
        box = QVBoxLayout()
        k = QLabel(name); k.setObjectName("metric")
        v = QLabel(initial); v.setObjectName("value")
        box.addWidget(k); box.addWidget(v)
        parent.addLayout(box, 1)
        return v

    def append_log(self, s):
        if s:
            self.log.appendPlainText(str(s).rstrip())

    def set_busy(self, busy, text=None):
        for b in (self.scan_btn, self.detect_btn, self.check_btn, self.sync_btn, self.gui_update_btn, self.flash_btn):
            b.setEnabled(not busy)
        if busy:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self._refresh_button_states()
        if text:
            self.state_label.setText(text)

    def _refresh_button_states(self):
        self.flash_btn.setEnabled(self.detected_chip is not None)
        self.sync_btn.setEnabled(self.detected_chip is not None)
        try:
            self.gui_update_btn.setEnabled(core.gui_update_available(APP_VERSION, self.remote_manifest))
        except Exception:
            self.gui_update_btn.setEnabled(False)

    def refresh_ports(self):
        current = self.port.currentData()
        self.port.clear()
        for dev, details in core.list_serial_ports():
            self.port.addItem(f"{dev}   {details}".rstrip(), dev)
        if current:
            idx = self.port.findData(current)
            if idx >= 0:
                self.port.setCurrentIndex(idx)
        self.append_log(f"Serial ports: {self.port.count()}")

    def start_job(self, fn, done, busy_text):
        self.set_busy(True, busy_text)
        job = Job(fn)
        job.signals.log.connect(self.append_log)
        job.signals.progress.connect(self.on_progress)
        job.signals.error.connect(self.job_error)
        job.signals.done.connect(lambda result: self.job_done(result, done))
        self.pool.start(job)

    @Slot(int,int,str)
    def on_progress(self, cur, total, text):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
        self.state_label.setText(text)

    def job_error(self, tb):
        self.append_log(tb)
        self.set_busy(False, "FAIL")
        QMessageBox.critical(self, "T500 Firmware Flasher", tb.splitlines()[-1] if tb else "Unknown error")

    def job_done(self, result, callback):
        self.set_busy(False)
        callback(result)

    def detect(self):
        port = self.port.currentData()
        if not port:
            QMessageBox.warning(self, "T500 Firmware Flasher", "Không tìm thấy cổng serial.")
            return
        def work(sig):
            chip, mac, out = core.detect_chip(port)
            sig.log.emit(out)
            return chip, mac
        self.start_job(work, self.detect_done, "ĐANG NHẬN DIỆN")

    def detect_done(self, result):
        chip, mac = result
        if chip not in ("ESP32", "ESP32-S3"):
            self.detected_chip = None
            self.chip_value.setText("Không hỗ trợ")
            self.state_label.setText("DETECT FAIL")
            return
        self.detected_chip = chip
        self.detected_mac = mac
        self.chip_value.setText(chip)
        self.mac_value.setText(mac)
        self.update_fw_labels()
        self.state_label.setText("DETECT PASS")
        self.append_log(f"Detected {chip} | MAC {mac}")
        self._refresh_button_states()

    def update_fw_labels(self):
        if not self.detected_chip:
            return
        chip = self.detected_chip
        self.fw_local_value.setText("v" + core.installed_firmware_version(chip))
        self.fw_latest_value.setText("v" + self.remote_manifest["firmware"][chip]["version"])

    def check_updates(self, silent=False):
        def work(sig):
            return core.fetch_manifest()
        def done(manifest):
            self.remote_manifest = manifest
            gui_new = core.gui_update_available(APP_VERSION, manifest)
            self.update_status.setText(
                f"Stable • GUI latest v{manifest['gui']['version']}" +
                (" • CÓ BẢN GUI MỚI" if gui_new else " • GUI đã mới nhất")
            )
            self.update_fw_labels()
            self._refresh_button_states()
            if not silent:
                self.append_log("Update manifest refreshed.")
        self.start_job(work, done, "ĐANG KIỂM TRA")

    def sync_firmware(self):
        if not self.detected_chip:
            return
        chip = self.detected_chip
        def work(sig):
            def progress(i, n, text):
                sig.progress.emit(i, n, text)
            path = core.sync_firmware(chip, self.remote_manifest, progress)
            return str(path)
        def done(path):
            self.update_fw_labels()
            self.state_label.setText("FW SYNC PASS")
            self.append_log(f"Firmware synced: {path}")
            QMessageBox.information(self, "Firmware", "Firmware đã được tải và kiểm tra SHA256 thành công.")
        self.start_job(work, done, "ĐANG TẢI FIRMWARE")

    def flash(self):
        if not self.detected_chip:
            return
        port = self.port.currentData()
        chip = self.detected_chip
        cfg = self.remote_manifest["firmware"][chip]
        reply = QMessageBox.question(
            self, "Xác nhận nạp",
            f"Chip: {chip}\nMAC: {self.detected_mac}\nFirmware: {cfg['display_name']} v{cfg['version']}\n\nTiếp tục nạp?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        def work(sig):
            ok, out = core.flash_firmware(port, chip, self.remote_manifest)
            sig.log.emit(out)
            if not ok:
                raise RuntimeError("Flash failed. Xem log kỹ thuật.")
            return True
        def done(_):
            self.state_label.setText("FLASH PASS")
            QMessageBox.information(self, "T500 Firmware Flasher", "Nạp firmware + verify thành công.")
        self.start_job(work, done, "ĐANG NẠP")

    def update_gui(self):
        if not core.gui_update_available(APP_VERSION, self.remote_manifest):
            QMessageBox.information(self, "Update", "GUI hiện tại đã là phiên bản mới nhất.")
            return
        new_ver = self.remote_manifest["gui"]["version"]
        if QMessageBox.question(self, "Cập nhật GUI", f"Tải và cài GUI v{new_ver}?") != QMessageBox.Yes:
            return
        def work(sig):
            def progress(cur, total):
                sig.progress.emit(cur, total, "ĐANG TẢI GUI")
            return str(core.download_gui_update(self.remote_manifest, progress))
        def done(path):
            try:
                core.schedule_self_replace(Path(path))
            except Exception as e:
                QMessageBox.warning(self, "Update", f"Đã tải bản mới tại:\n{path}\n\nKhông thể tự thay executable: {e}")
                return
            QApplication.quit()
        self.start_job(work, done, "ĐANG TẢI GUI")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("T500 Firmware Flasher")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
