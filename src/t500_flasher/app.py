from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget
)

from . import APP_VERSION
from . import core


QSS = """
QWidget {
    background: #F3F5F7;
    color: #24313D;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}
QMainWindow { background: #F3F5F7; }

QFrame#topBar {
    background: #FFFFFF;
    border: 1px solid #DDE3E8;
    border-radius: 18px;
}
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #DDE3E8;
    border-radius: 14px;
}
QFrame#metricCard {
    background: #F8FAFB;
    border: 1px solid #E4E9ED;
    border-radius: 11px;
}
QFrame#flashCard {
    background: #FFFDF5;
    border: 1px solid #E8DCA8;
    border-radius: 14px;
}

QLabel#eyebrow {
    color: #637381;
    font-size: 11px;
    font-weight: 700;
}
QLabel#title {
    color: #1B2733;
    font-size: 28px;
    font-weight: 750;
}
QLabel#subtitle {
    color: #687784;
    font-size: 13px;
}
QLabel#sectionTitle {
    color: #1F2B36;
    font-size: 14px;
    font-weight: 700;
}
QLabel#sectionHint {
    color: #7A8792;
    font-size: 12px;
}
QLabel#metric {
    color: #788692;
    font-size: 10px;
    font-weight: 700;
}
QLabel#value {
    color: #1F2B36;
    font-size: 15px;
    font-weight: 700;
}
QLabel#statusBadge {
    background: #EEF4F6;
    color: #1B7284;
    border: 1px solid #CADDE2;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 700;
}
QLabel#versionBadge {
    background: #FFF6CC;
    color: #705A00;
    border: 1px solid #E8D374;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: 700;
}

QComboBox {
    background: #FFFFFF;
    border: 1px solid #C9D2D9;
    border-radius: 9px;
    padding: 9px 10px;
    min-height: 20px;
    selection-background-color: #D7EDF2;
}
QComboBox:hover { border-color: #8CA0AD; }
QComboBox:focus { border: 1px solid #247F93; }
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #C9D2D9;
    selection-background-color: #D7EDF2;
    selection-color: #1F2B36;
}

QPushButton {
    background: #FFFFFF;
    color: #2A3945;
    border: 1px solid #C9D2D9;
    border-radius: 9px;
    padding: 9px 14px;
    font-weight: 650;
}
QPushButton:hover {
    background: #F7F9FA;
    border-color: #94A4AF;
}
QPushButton:pressed { background: #EEF2F4; }
QPushButton:disabled {
    background: #F1F3F5;
    color: #A6B0B8;
    border-color: #E0E5E9;
}

QPushButton#primary {
    background: #19788C;
    color: #FFFFFF;
    border: 1px solid #19788C;
}
QPushButton#primary:hover {
    background: #146A7C;
    border-color: #146A7C;
}
QPushButton#secondary {
    background: #EFF6F8;
    color: #176C7D;
    border: 1px solid #BFD8DE;
}
QPushButton#secondary:hover {
    background: #E2F0F3;
    border-color: #8DBDC8;
}
QPushButton#flash {
    background: #F2C400;
    color: #2F2A13;
    border: 1px solid #D8AE00;
    border-radius: 11px;
    padding: 12px 18px;
    font-size: 14px;
    font-weight: 800;
}
QPushButton#flash:hover {
    background: #E7BA00;
    border-color: #C69F00;
}

QPlainTextEdit {
    background: #FBFCFD;
    color: #33424E;
    border: 1px solid #DDE3E8;
    border-radius: 11px;
    padding: 9px;
    font-family: "JetBrains Mono", "Consolas", "Monospace";
    font-size: 12px;
}
QProgressBar {
    background: #ECEFF2;
    border: 0;
    border-radius: 5px;
    min-height: 10px;
    max-height: 10px;
    text-align: center;
}
QProgressBar::chunk {
    background: #19788C;
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
        self.remote_manifest = core.read_bundled_manifest()
        self.detected_chip = None
        self.detected_mac = "-"

        self.setWindowTitle(f"T500 ESP32 Flasher v{APP_VERSION}")
        self.setMinimumSize(1040, 790)
        self.resize(1120, 860)
        self.setStyleSheet(QSS)

        icon_path = core.bundle_root() / "assets/logo.png"
        mark_path = core.bundle_root() / "assets/t500_real_mark.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(13)

        # Header: clean product identity, no fantasy artwork.
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        header = QHBoxLayout(top_bar)
        header.setContentsMargins(18, 15, 18, 15)
        header.setSpacing(18)

        if mark_path.exists():
            mark = QSvgWidget(str(mark_path))
            mark.setFixedSize(235, 128)
            header.addWidget(mark, 0, Qt.AlignVCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        eyebrow = QLabel("AUBOT T500  /  MAIN CONTROLLER SERVICE")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("ESP32 Firmware Flasher")
        title.setObjectName("title")
        subtitle = QLabel("Nhận diện đúng chip • Firmware đã kiểm chứng • Nạp và verify bằng esptool")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        title_col.addStretch(1)
        header.addLayout(title_col, 1)

        badges = QVBoxLayout()
        badges.setSpacing(7)
        self.gui_badge = QLabel(f"GUI v{APP_VERSION}")
        self.gui_badge.setObjectName("versionBadge")
        channel_badge = QLabel("STABLE")
        channel_badge.setObjectName("statusBadge")
        badges.addWidget(self.gui_badge, 0, Qt.AlignRight)
        badges.addWidget(channel_badge, 0, Qt.AlignRight)
        badges.addStretch(1)
        header.addLayout(badges)
        layout.addWidget(top_bar)

        # Connection/device card.
        device_card = QFrame()
        device_card.setObjectName("card")
        device = QVBoxLayout(device_card)
        device.setContentsMargins(16, 14, 16, 16)
        device.setSpacing(12)

        title_row = QHBoxLayout()
        section_title = QLabel("Kết nối & nhận diện bộ điều khiển")
        section_title.setObjectName("sectionTitle")
        title_row.addWidget(section_title)
        title_row.addStretch(1)
        self.state_label = QLabel("SẴN SÀNG")
        self.state_label.setObjectName("statusBadge")
        title_row.addWidget(self.state_label)
        device.addLayout(title_row)

        hint = QLabel("Cắm cáp USB/serial, chọn đúng cổng rồi để phần mềm tự nhận diện ESP32 Classic hoặc ESP32-S3.")
        hint.setObjectName("sectionHint")
        device.addWidget(hint)

        connect_row = QHBoxLayout()
        connect_row.setSpacing(8)
        port_label = QLabel("Cổng serial")
        port_label.setObjectName("eyebrow")
        connect_row.addWidget(port_label)

        self.port = QComboBox()
        self.port.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        connect_row.addWidget(self.port, 1)

        self.scan_btn = QPushButton("Quét lại")
        self.detect_btn = QPushButton("Nhận diện chip")
        self.detect_btn.setObjectName("primary")
        connect_row.addWidget(self.scan_btn)
        connect_row.addWidget(self.detect_btn)
        device.addLayout(connect_row)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(10)
        metrics.setVerticalSpacing(10)
        self.chip_value = self.add_metric(metrics, 0, 0, "CHIP", "Chưa nhận diện")
        self.mac_value = self.add_metric(metrics, 0, 1, "MAC", "-")
        self.fw_local_value = self.add_metric(metrics, 0, 2, "FIRMWARE LOCAL", "-")
        self.fw_latest_value = self.add_metric(metrics, 0, 3, "FIRMWARE MỚI NHẤT", "-")
        device.addLayout(metrics)
        layout.addWidget(device_card)

        # Update card.
        update_card = QFrame()
        update_card.setObjectName("card")
        update = QVBoxLayout(update_card)
        update.setContentsMargins(16, 14, 16, 15)
        update.setSpacing(10)

        update_header = QHBoxLayout()
        update_title = QLabel("Cập nhật")
        update_title.setObjectName("sectionTitle")
        update_header.addWidget(update_title)
        update_header.addStretch(1)
        self.update_status = QLabel("Stable • chưa kiểm tra cập nhật")
        self.update_status.setObjectName("sectionHint")
        update_header.addWidget(self.update_status)
        update.addLayout(update_header)

        update_buttons = QHBoxLayout()
        update_buttons.setSpacing(8)
        self.check_btn = QPushButton("Kiểm tra cập nhật")
        self.sync_btn = QPushButton("Đồng bộ firmware")
        self.sync_btn.setObjectName("secondary")
        self.gui_update_btn = QPushButton("Cập nhật ứng dụng")
        self.gui_update_btn.setObjectName("secondary")
        self.sync_btn.setEnabled(False)
        self.gui_update_btn.setEnabled(False)
        update_buttons.addWidget(self.check_btn)
        update_buttons.addWidget(self.sync_btn)
        update_buttons.addWidget(self.gui_update_btn)
        update_buttons.addStretch(1)
        update.addLayout(update_buttons)
        layout.addWidget(update_card)

        # Flash action card.
        flash_card = QFrame()
        flash_card.setObjectName("flashCard")
        flash_layout = QVBoxLayout(flash_card)
        flash_layout.setContentsMargins(16, 14, 16, 15)
        flash_layout.setSpacing(10)

        flash_header = QHBoxLayout()
        flash_text = QVBoxLayout()
        flash_title = QLabel("Nạp firmware")
        flash_title.setObjectName("sectionTitle")
        flash_hint = QLabel("Chỉ nạp firmware tương ứng với chip đã nhận diện. Không full-chip erase mặc định.")
        flash_hint.setObjectName("sectionHint")
        flash_text.addWidget(flash_title)
        flash_text.addWidget(flash_hint)
        flash_header.addLayout(flash_text, 1)

        self.flash_btn = QPushButton("NẠP & VERIFY FIRMWARE")
        self.flash_btn.setObjectName("flash")
        self.flash_btn.setMinimumWidth(250)
        self.flash_btn.setMinimumHeight(45)
        self.flash_btn.setEnabled(False)
        flash_header.addWidget(self.flash_btn, 0, Qt.AlignVCenter)
        flash_layout.addLayout(flash_header)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        flash_layout.addWidget(self.progress)
        layout.addWidget(flash_card)

        # Technical log.
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 13, 16, 16)
        log_layout.setSpacing(8)
        log_title = QLabel("Nhật ký kỹ thuật")
        log_title.setObjectName("sectionTitle")
        log_layout.addWidget(log_title)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Thông tin nhận diện, tải firmware và esptool sẽ xuất hiện ở đây…")
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
        box.setContentsMargins(12, 9, 12, 10)
        box.setSpacing(2)
        k = QLabel(name)
        k.setObjectName("metric")
        v = QLabel(initial)
        v.setObjectName("value")
        v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        box.addWidget(k)
        box.addWidget(v)
        grid.addWidget(card, row, col)
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

    def start_job(self, fn, done, busy_text, error_handler=None):
        self.set_busy(True, busy_text)
        job = Job(fn)
        job.signals.log.connect(self.append_log)
        job.signals.progress.connect(self.on_progress)
        job.signals.error.connect(error_handler or self.job_error)
        job.signals.done.connect(lambda result: self.job_done(result, done))
        self.pool.start(job)

    @Slot(int, int, str)
    def on_progress(self, cur, total, text):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(cur)
        self.state_label.setText(text)

    def silent_job_error(self, tb):
        self.append_log("Update check skipped: " + (tb.splitlines()[-1] if tb else "unknown error"))
        self.set_busy(False, "SẴN SÀNG")

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
                (" • có bản GUI mới" if gui_new else " • GUI đã mới nhất")
            )
            self.update_fw_labels()
            self._refresh_button_states()
            if not silent:
                self.append_log("Update manifest refreshed.")

        self.start_job(
            work,
            done,
            "ĐANG KIỂM TRA",
            error_handler=self.silent_job_error if silent else None,
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

        self.start_job(work, done, "ĐANG TẢI FIRMWARE")

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
                QMessageBox.warning(
                    self,
                    "Update",
                    f"Đã tải bản mới tại:\n{path}\n\nKhông thể tự thay executable: {e}",
                )
                return
            QApplication.quit()

        self.start_job(work, done, "ĐANG TẢI GUI")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("T500 Firmware Flasher")
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
