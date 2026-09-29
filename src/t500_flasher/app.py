from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget
)

from . import APP_VERSION
from . import core


QSS = """
QWidget {
    background: #EEF5FB;
    color: #15324A;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background: #EEF5FB;
}
QLabel {
    background: transparent;
}

QFrame#hero {
    background: #E5F3FF;
    border: 1px solid #C7DEEE;
    border-radius: 16px;
}
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #D6E4EF;
    border-radius: 14px;
}
QFrame#metricCard {
    background: #F7FBFE;
    border: 1px solid #DDEAF3;
    border-radius: 10px;
}
QFrame#flashCard {
    background: #FFFFFF;
    border: 1px solid #D7E4EF;
    border-radius: 14px;
}

QLabel#eyebrow {
    color: #59748B;
    font-size: 11px;
    font-weight: 700;
}
QLabel#heroTitle {
    color: #123858;
    font-size: 21px;
    font-weight: 800;
}
QLabel#heroSubtitle {
    color: #688197;
    font-size: 12px;
}
QLabel#sectionTitle {
    color: #143B5D;
    font-size: 14px;
    font-weight: 800;
}
QLabel#sectionHint {
    color: #6F879B;
    font-size: 12px;
}
QLabel#metric {
    color: #748EA4;
    font-size: 10px;
    font-weight: 800;
}
QLabel#value {
    color: #163955;
    font-size: 15px;
    font-weight: 800;
}
QLabel#statusBadge {
    background: #E9F8F0;
    color: #128845;
    border: 1px solid #B9E7CC;
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 800;
}
QLabel#versionBadge {
    background: #EAF4FC;
    color: #17689F;
    border: 1px solid #C4DFF0;
    border-radius: 14px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 800;
}
QLabel#flashStatus {
    color: #607C93;
    font-size: 11px;
    font-weight: 800;
    padding: 2px 8px;
}

QComboBox {
    background: #FFFFFF;
    color: #15324A;
    border: 1px solid #C8DBE9;
    border-radius: 9px;
    padding: 8px 10px;
    min-height: 22px;
    selection-background-color: #DFF0FC;
}
QComboBox:hover { border-color: #7EB4DA; }
QComboBox:focus { border: 1px solid #1683C7; }
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #C8DBE9;
    selection-background-color: #DFF0FC;
    selection-color: #15324A;
}

QPushButton {
    background: #FFFFFF;
    color: #1E4D71;
    border: 1px solid #C7DBEA;
    border-radius: 9px;
    padding: 9px 14px;
    font-weight: 750;
}
QPushButton:hover {
    background: #F4FAFE;
    border-color: #7FB6DB;
}
QPushButton:pressed {
    background: #E7F3FB;
}
QPushButton:disabled {
    background: #F2F6F9;
    color: #9AABBA;
    border-color: #DFE8EE;
}
QPushButton#primary {
    background: #1788D4;
    color: #FFFFFF;
    border: 1px solid #1788D4;
}
QPushButton#primary:hover {
    background: #0F77BE;
    border-color: #0F77BE;
}
QPushButton#secondary {
    background: #EFF7FD;
    color: #176CA8;
    border: 1px solid #BCD9ED;
}
QPushButton#secondary:hover {
    background: #E2F1FB;
    border-color: #8FC3E4;
}
QPushButton#flash {
    background: #1288D8;
    color: #FFFFFF;
    border: 1px solid #1288D8;
    border-radius: 10px;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 850;
}
QPushButton#flash:hover {
    background: #0876C3;
    border-color: #0876C3;
}
QPushButton#verify {
    background: #1EB466;
    color: #FFFFFF;
    border: 1px solid #1EB466;
}
QPushButton#verify:hover {
    background: #179956;
    border-color: #179956;
}

QPlainTextEdit {
    background: #FBFDFE;
    color: #24455F;
    border: 1px solid #D5E3ED;
    border-radius: 10px;
    padding: 9px;
    font-family: "Consolas", "JetBrains Mono", monospace;
    font-size: 12px;
}
QProgressBar {
    background: #E7EFF5;
    border: 0;
    border-radius: 5px;
    min-height: 10px;
    max-height: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background: #1688D4;
    border-radius: 5px;
}
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
        self._jobs = set()
        self.remote_manifest = core.read_bundled_manifest()
        self.detected_chip = None
        self.detected_mac = "-"

        self.setWindowTitle(f"T500 ESP32 Flasher v{APP_VERSION}")
        self.setMinimumSize(1120, 820)
        self.resize(1240, 900)
        self.setStyleSheet(QSS)

        app_icon = core.bundle_root() / "assets/logo_app.png"
        if not app_icon.exists():
            app_icon = core.bundle_root() / "assets/logo.png"
        if app_icon.exists():
            self.setWindowIcon(QIcon(str(app_icon)))

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Hero banner inspired by the clean B300 tester layout.
        hero = QFrame()
        hero.setObjectName("hero")
        header = QHBoxLayout(hero)
        header.setContentsMargins(14, 10, 14, 10)
        header.setSpacing(18)

        hero_path = core.bundle_root() / "assets/t500_hero.png"
        if hero_path.exists():
            art = QLabel()
            pm = QPixmap(str(hero_path))
            art.setPixmap(pm.scaled(505, 168, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            art.setFixedSize(515, 170)
            art.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            art.setStyleSheet("background: transparent; border: 0;")
            header.addWidget(art, 0, Qt.AlignVCenter)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(3)
        eyebrow = QLabel("T500 MAIN CONTROLLER SERVICE")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("ESP32 Firmware Flasher")
        title.setObjectName("heroTitle")
        subtitle = QLabel("Detect · Firmware Sync · Flash · Verify")
        subtitle.setObjectName("heroSubtitle")
        hero_text.addWidget(eyebrow)
        hero_text.addWidget(title)
        hero_text.addWidget(subtitle)
        hero_text.addStretch(1)
        header.addLayout(hero_text, 1)

        badges = QHBoxLayout()
        badges.setSpacing(7)
        self.gui_badge = QLabel(f"v{APP_VERSION}")
        self.gui_badge.setObjectName("versionBadge")
        self.gui_badge.setAlignment(Qt.AlignCenter)
        self.gui_badge.setFixedSize(72, 30)

        self.state_label = QLabel("READY")
        self.state_label.setObjectName("statusBadge")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setFixedSize(92, 30)

        badges.addWidget(self.gui_badge, 0, Qt.AlignVCenter)
        badges.addWidget(self.state_label, 0, Qt.AlignVCenter)
        header.addLayout(badges)
        layout.addWidget(hero)

        # Device / connection section
        device_card = QFrame()
        device_card.setObjectName("card")
        device = QVBoxLayout(device_card)
        device.setContentsMargins(16, 13, 16, 15)
        device.setSpacing(10)

        row_title = QHBoxLayout()
        st = QLabel("🔌  KẾT NỐI & NHẬN DIỆN MAIN")
        st.setObjectName("sectionTitle")
        row_title.addWidget(st)
        row_title.addStretch(1)
        device.addLayout(row_title)

        conn = QHBoxLayout()
        conn.setSpacing(8)

        port_lbl = QLabel("Serial Port")
        port_lbl.setObjectName("eyebrow")
        conn.addWidget(port_lbl)

        self.port = QComboBox()
        self.port.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        conn.addWidget(self.port, 1)

        self.scan_btn = QPushButton("QUÉT LẠI")
        self.detect_btn = QPushButton("NHẬN DIỆN CHIP")
        self.detect_btn.setObjectName("primary")
        conn.addWidget(self.scan_btn)
        conn.addWidget(self.detect_btn)
        device.addLayout(conn)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(10)
        metrics.setVerticalSpacing(10)
        self.chip_value = self.add_metric(metrics, 0, 0, "CHIP", "Chưa nhận diện")
        self.mac_value = self.add_metric(metrics, 0, 1, "MAC", "-")
        self.fw_local_value = self.add_metric(metrics, 0, 2, "FIRMWARE LOCAL", "-")
        self.fw_latest_value = self.add_metric(metrics, 0, 3, "FIRMWARE LATEST", "-")
        device.addLayout(metrics)
        layout.addWidget(device_card)

        # Firmware update section
        update_card = QFrame()
        update_card.setObjectName("card")
        update = QVBoxLayout(update_card)
        update.setContentsMargins(16, 13, 16, 15)
        update.setSpacing(10)

        update_header = QHBoxLayout()
        ut = QLabel("☁  FIRMWARE & UPDATE")
        ut.setObjectName("sectionTitle")
        update_header.addWidget(ut)
        update_header.addStretch(1)
        self.update_status = QLabel("Stable • chưa kiểm tra cập nhật")
        self.update_status.setObjectName("sectionHint")
        update_header.addWidget(self.update_status)
        update.addLayout(update_header)

        update_buttons = QHBoxLayout()
        update_buttons.setSpacing(8)
        self.check_btn = QPushButton("KIỂM TRA CẬP NHẬT")
        self.sync_btn = QPushButton("ĐỒNG BỘ FIRMWARE")
        self.sync_btn.setObjectName("secondary")
        self.gui_update_btn = QPushButton("CẬP NHẬT ỨNG DỤNG")
        self.gui_update_btn.setObjectName("secondary")
        self.sync_btn.setEnabled(False)
        self.gui_update_btn.setEnabled(False)
        update_buttons.addWidget(self.check_btn)
        update_buttons.addWidget(self.sync_btn)
        update_buttons.addWidget(self.gui_update_btn)
        update_buttons.addStretch(1)
        update.addLayout(update_buttons)
        layout.addWidget(update_card)

        # Flash action section
        flash_card = QFrame()
        flash_card.setObjectName("flashCard")
        flash_layout = QVBoxLayout(flash_card)
        flash_layout.setContentsMargins(16, 13, 16, 15)
        flash_layout.setSpacing(10)

        fh = QHBoxLayout()
        ft = QVBoxLayout()
        flash_title = QLabel("⚡  NẠP & VERIFY FIRMWARE")
        flash_title.setObjectName("sectionTitle")
        flash_hint = QLabel("Firmware được chọn tự động theo chip đã nhận diện. Chỉ ghi flash sau khi bấm BẮT ĐẦU FLASH và xác nhận.")
        flash_hint.setObjectName("sectionHint")
        self.flash_status = QLabel("CHƯA NẠP")
        self.flash_status.setObjectName("flashStatus")
        self.flash_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ft.addWidget(flash_title)
        ft.addWidget(flash_hint)
        ft.addWidget(self.flash_status)
        fh.addLayout(ft, 1)

        self.flash_btn = QPushButton("▶  BẮT ĐẦU FLASH")
        self.flash_btn.setObjectName("flash")
        self.flash_btn.setMinimumWidth(240)
        self.flash_btn.setMinimumHeight(44)
        self.flash_btn.setEnabled(False)
        fh.addWidget(self.flash_btn, 0, Qt.AlignVCenter)
        flash_layout.addLayout(fh)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        flash_layout.addWidget(self.progress)
        layout.addWidget(flash_card)

        # Technical log
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 12, 16, 14)
        log_layout.setSpacing(8)

        lt = QLabel("▤  EVENT / TECHNICAL LOG")
        lt.setObjectName("sectionTitle")
        log_layout.addWidget(lt)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Detect / sync / flash / verify log sẽ hiển thị tại đây…")
        log_layout.addWidget(self.log, 1)
        layout.addWidget(log_card, 1)

        self.scan_btn.clicked.connect(self.refresh_ports)
        self.detect_btn.clicked.connect(self.detect)
        self.check_btn.clicked.connect(self.check_updates)
        self.sync_btn.clicked.connect(self.sync_firmware)
        self.gui_update_btn.clicked.connect(self.update_gui)
        self.flash_btn.clicked.connect(self.flash)

        self.refresh_ports()
        self.append_log(f"T500 Firmware Flasher v{APP_VERSION} started.")
        self.check_updates(silent=True)

    def add_metric(self, grid, row, col, name, initial):
        card = QFrame()
        card.setObjectName("metricCard")
        box = QVBoxLayout(card)
        box.setContentsMargins(12, 8, 12, 9)
        box.setSpacing(2)
        k = QLabel(name)
        k.setObjectName("metric")
        k.setAlignment(Qt.AlignCenter)
        v = QLabel(initial)
        v.setObjectName("value")
        v.setAlignment(Qt.AlignCenter)
        v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        box.addWidget(k)
        box.addWidget(v)
        grid.addWidget(card, row, col)
        return v

    def append_log(self, s):
        if s:
            self.log.appendPlainText(str(s).rstrip())

    def set_busy(self, busy, text=None, show_progress=False):
        for b in (self.scan_btn, self.detect_btn, self.check_btn, self.sync_btn, self.gui_update_btn, self.flash_btn):
            b.setEnabled(not busy)

        if busy and show_progress:
            self.progress.show()
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setFormat("%p%")
        elif not busy:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.hide()
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

    def start_job(self, fn, done, busy_text=None, error_handler=None, show_progress=False, background=False):
        if not background:
            self.set_busy(True, busy_text, show_progress=show_progress)

        job = Job(fn)
        self._jobs.add(job)

        job.signals.log.connect(self.append_log)
        job.signals.progress.connect(self.on_progress)

        def finish_ok(result, _job=job):
            try:
                if background:
                    self.background_job_done(result, done)
                else:
                    self.job_done(result, done)
            finally:
                self._jobs.discard(_job)

        def finish_error(tb, _job=job):
            try:
                (error_handler or self.job_error)(tb)
            finally:
                self._jobs.discard(_job)

        job.signals.error.connect(finish_error)
        job.signals.done.connect(finish_ok)
        self.pool.start(job)

    @Slot(int, int, str)
    def on_progress(self, cur, total, text):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
        self.state_label.setText(text)
        if text.startswith("FLASHING"):
            pct = int((cur * 100) / total) if total else 0
            self.flash_status.setText(f"ĐANG NẠP • {pct}%")

    def silent_job_error(self, tb):
        self.append_log("Update check skipped: " + (tb.splitlines()[-1] if tb else "unknown error"))

    def job_error(self, tb):
        self.append_log(tb)
        was_flashing = self.state_label.text().startswith("FLASHING")
        self.set_busy(False, "FAIL")
        if was_flashing:
            self.flash_status.setText("FLASH FAIL")
        QMessageBox.critical(self, "T500 Firmware Flasher", tb.splitlines()[-1] if tb else "Unknown error")

    def job_done(self, result, callback):
        self.set_busy(False)
        callback(result)

    def background_job_done(self, result, callback):
        callback(result)

    def detect(self):
        port = self.port.currentData()
        if not port:
            QMessageBox.warning(self, "T500 Firmware Flasher", "Không tìm thấy cổng serial.")
            return

        def work(sig):
            # Return chip/MAC/log as one atomic result so the visible metrics
            # cannot lag behind a separately queued log signal.
            return core.detect_chip(port)

        self.start_job(work, self.detect_done, "DETECTING")

    def detect_done(self, result):
        chip, mac, out = result
        self.append_log(out)
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
                (" • có bản GUI mới" if gui_new else " • GUI đã mới nhất")
            )
            self.update_fw_labels()
            self._refresh_button_states()
            if not silent:
                self.append_log("Update manifest refreshed.")

        self.start_job(
            work,
            done,
            None if silent else "CHECKING",
            error_handler=self.silent_job_error if silent else None,
            background=silent,
        )

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

        self.start_job(work, done, "SYNCING")

    def flash(self):
        if not self.detected_chip:
            return
        port = self.port.currentData()
        chip = self.detected_chip
        cfg = self.remote_manifest["firmware"][chip]
        reply = QMessageBox.question(
            self,
            "Xác nhận nạp",
            f"Chip: {chip}\nMAC: {self.detected_mac}\nFirmware: {cfg['display_name']} v{cfg['version']}\n\nTiếp tục nạp?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.flash_status.setText("ĐANG CHỜ XÁC NHẬN NẠP...")

        def work(sig):
            def flash_progress(percent):
                sig.progress.emit(percent, 100, f"FLASHING {percent}%")

            ok, out = core.flash_firmware(
                port,
                chip,
                self.remote_manifest,
                progress=flash_progress,
            )
            sig.log.emit(out)
            if not ok:
                raise RuntimeError("Flash failed. Xem log kỹ thuật.")
            return True

        def done(_):
            self.state_label.setText("FLASH PASS")
            self.flash_status.setText("THÀNH CÔNG • 100%")
            self.progress.show()
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            self.progress.setFormat("100%")
            QTimer.singleShot(5000, self.progress.hide)
            QMessageBox.information(self, "T500 Firmware Flasher", "Nạp firmware + verify thành công.")

        self.flash_status.setText("ĐANG NẠP • 0%")
        self.start_job(work, done, "FLASHING 0%", show_progress=True)

    def update_gui(self):
        if not core.gui_update_available(APP_VERSION, self.remote_manifest):
            QMessageBox.information(self, "Update", "GUI hiện tại đã là phiên bản mới nhất.")
            return
        new_ver = self.remote_manifest["gui"]["version"]
        if QMessageBox.question(self, "Cập nhật GUI", f"Tải và cài GUI v{new_ver}?") != QMessageBox.Yes:
            return

        def work(sig):
            def progress(cur, total):
                sig.progress.emit(cur, total, "DOWNLOADING")
            return str(core.download_gui_update(self.remote_manifest, progress))

        def done(path):
            try:
                core.schedule_self_replace(Path(path))
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Update",
                    f"Đã tải bản mới tại:\n{path}\n\nKhông thể tự thay executable: {e}",
                )
                return
            QApplication.quit()

        self.start_job(work, done, "DOWNLOADING")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("T500 Firmware Flasher")
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
