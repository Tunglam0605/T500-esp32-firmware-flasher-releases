from __future__ import annotations

import datetime
import html
import re
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget
)

from . import APP_VERSION
from . import core


QSS = """
QWidget {
    background: #EEF5FB;
    color: #15324A;
    font-family: "Segoe UI", "Ubuntu", -apple-system, sans-serif;
    font-size: 12px;
}
QMainWindow {
    background: #EEF5FB;
}
QLabel {
    background: transparent;
}

QFrame#hero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DEEEFC, stop:0.5 #F3F8FD, stop:1 #D6EBFB);
    border: 1px solid #C4DDF0;
    border-radius: 12px;
}
QFrame#card {
    background: #FFFFFF;
    border: 1px solid #D6E4EF;
    border-radius: 12px;
}
QFrame#metricCard {
    background: #F7FBFE;
    border: 1px solid #DEEBF4;
    border-radius: 10px;
}

QLabel#heroTitle {
    color: #0C2F55;
    font-size: 19px;
    font-weight: 800;
}
QLabel#heroSubtitle {
    color: #5E7A94;
    font-size: 12px;
    font-weight: 500;
}
QLabel#serviceTag {
    color: #7995AC;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QLabel#sectionTitle {
    color: #0C2F55;
    font-size: 13px;
    font-weight: 800;
}
QLabel#sectionHint {
    color: #7690A5;
    font-size: 11px;
}
QLabel#portLabel {
    color: #506A82;
    font-size: 12px;
    font-weight: 600;
}
QLabel#metric {
    color: #7894AA;
    font-size: 10px;
    font-weight: 800;
}
QLabel#value {
    color: #0C2F55;
    font-size: 16px;
    font-weight: 800;
}
QLabel#versionBadge {
    background: #EAF4FC;
    color: #1688D4;
    border: 1px solid #C8E1F4;
    border-radius: 12px;
    padding: 3px 11px;
    font-size: 11px;
    font-weight: 800;
}
QLabel#statusBadge {
    background: #EAF8EF;
    color: #18A957;
    border: 1px solid #BAEBD0;
    border-radius: 12px;
    padding: 3px 11px;
    font-size: 11px;
    font-weight: 800;
}
QLabel#flashStatusPill {
    background: #EBF1F7;
    color: #6E8599;
    border: 1px solid #D2E0EC;
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 800;
}

QComboBox {
    background: #FFFFFF;
    color: #15324A;
    border: 1px solid #CFDFEC;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 20px;
    selection-background-color: #DFF0FC;
}
QComboBox:hover { border-color: #8FC3E4; }
QComboBox:focus { border: 1px solid #1688D4; }
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #CFDFEC;
    selection-background-color: #DFF0FC;
    selection-color: #15324A;
}

QPushButton {
    background: #FFFFFF;
    color: #1688D4;
    border: 1px solid #BCD7EC;
    border-radius: 8px;
    padding: 7px 15px;
    font-size: 12px;
    font-weight: 750;
}
QPushButton:hover {
    background: #F2F8FD;
    border-color: #8FC3E4;
}
QPushButton:pressed {
    background: #E4F1FA;
}
QPushButton:disabled {
    background: #F7FAFC;
    color: #A0B2C2;
    border-color: #E2EBF1;
}

QPushButton#primary {
    background: #1688D4;
    color: #FFFFFF;
    border: 1px solid #1688D4;
}
QPushButton#primary:hover {
    background: #0F77BE;
    border-color: #0F77BE;
}
QPushButton#primary:pressed {
    background: #0C65A2;
}

QPushButton#secondary {
    background: #FFFFFF;
    color: #1688D4;
    border: 1px solid #BCD7EC;
}

QPushButton#secondarySmall {
    background: #FFFFFF;
    color: #1688D4;
    border: 1px solid #CFDFEC;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}
QPushButton#secondarySmall:hover {
    background: #F2F8FD;
    border-color: #8FC3E4;
}

QPushButton#flashBtn {
    background: #1688D4;
    color: #FFFFFF;
    border: 1px solid #1688D4;
    border-radius: 8px;
    padding: 9px 24px;
    font-size: 13px;
    font-weight: 850;
}
QPushButton#flashBtn:hover {
    background: #0F77BE;
    border-color: #0F77BE;
}
QPushButton#flashBtn:pressed {
    background: #0C65A2;
}
QPushButton#flashBtn:disabled {
    background: #E5EEF5;
    color: #A3B5C4;
    border-color: #D6E3ED;
}

QTextEdit {
    background: #FFFFFF;
    color: #1B3650;
    border: 1px solid #D6E4EF;
    border-radius: 8px;
    padding: 8px 10px;
    font-family: "Consolas", "JetBrains Mono", monospace;
    font-size: 11px;
}

QProgressBar {
    background: #E2ECF3;
    border: 0;
    border-radius: 4px;
    min-height: 8px;
    max-height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: #1688D4;
    border-radius: 4px;
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
            res = self.fn(self.signals)
            try:
                self.signals.done.emit(res)
            except RuntimeError:
                pass
        except Exception:
            try:
                self.signals.error.emit(traceback.format_exc())
            except RuntimeError:
                pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self._jobs = set()
        self.remote_manifest = core.read_bundled_manifest()
        self.detected_chip = None
        self.detected_mac = "-"

        self.setWindowTitle("T500 ESP32 Flasher")
        self.setMinimumSize(980, 560)
        self.resize(1024, 576)
        self.setStyleSheet(QSS)

        app_icon = core.bundle_root() / "assets/logo_app.png"
        if not app_icon.exists():
            app_icon = core.bundle_root() / "assets/logo.png"
        if app_icon.exists():
            self.setWindowIcon(QIcon(str(app_icon)))

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # ---------------- HERO HEADER ----------------
        hero = QFrame()
        hero.setObjectName("hero")
        header = QHBoxLayout(hero)
        header.setContentsMargins(12, 6, 16, 6)
        header.setSpacing(14)

        # Left: T500 Hero Banner
        hero_path = core.bundle_root() / "assets/t500_hero.png"
        if hero_path.exists():
            art = QLabel()
            pm = QPixmap(str(hero_path))
            art.setPixmap(pm.scaledToHeight(116, Qt.SmoothTransformation))
            art.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            art.setStyleSheet("background: transparent; border: 0;")
            header.addWidget(art, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Center: AUBOT Logo + Title + Subtitle
        center_box = QVBoxLayout()
        center_box.setSpacing(2)
        center_box.setAlignment(Qt.AlignCenter)

        aubot_path = core.bundle_root() / "assets/aubot_logo.png"
        if aubot_path.exists():
            aubot_lbl = QLabel()
            aubot_pm = QPixmap(str(aubot_path))
            aubot_lbl.setPixmap(aubot_pm.scaledToHeight(30, Qt.SmoothTransformation))
            aubot_lbl.setAlignment(Qt.AlignCenter)
            aubot_lbl.setStyleSheet("background: transparent; border: 0;")
            center_box.addWidget(aubot_lbl)

        title = QLabel("ESP32 Firmware Flasher")
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignCenter)
        center_box.addWidget(title)

        sub = QLabel("Detect • Firmware Sync • Flash • Verify")
        sub.setObjectName("heroSubtitle")
        sub.setAlignment(Qt.AlignCenter)
        center_box.addWidget(sub)
        header.addLayout(center_box, 1)

        # Hero vertical separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setStyleSheet("color: #D3E4F2; background: #D3E4F2; width: 1px; max-width: 1px; margin: 10px 6px;")
        header.addWidget(sep1)

        # Right: Version pill + Status pill + Service tag
        right_box = QVBoxLayout()
        right_box.setSpacing(5)
        right_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        badges = QHBoxLayout()
        badges.setSpacing(6)
        badges.setAlignment(Qt.AlignRight)

        self.gui_badge = QLabel(f"v{APP_VERSION}")
        self.gui_badge.setObjectName("versionBadge")
        self.gui_badge.setAlignment(Qt.AlignCenter)

        self.state_label = QLabel("● READY")
        self.state_label.setObjectName("statusBadge")
        self.state_label.setAlignment(Qt.AlignCenter)

        badges.addWidget(self.gui_badge, 0, Qt.AlignVCenter)
        badges.addWidget(self.state_label, 0, Qt.AlignVCenter)
        right_box.addLayout(badges)

        service_lbl = QLabel("T500 MAIN CONTROLLER SERVICE")
        service_lbl.setObjectName("serviceTag")
        service_lbl.setAlignment(Qt.AlignRight)
        right_box.addWidget(service_lbl)

        header.addLayout(right_box, 0)
        layout.addWidget(hero)

        # ---------------- SECTION 1: CONNECTION & CHIP ----------------
        device_card = QFrame()
        device_card.setObjectName("card")
        device = QVBoxLayout(device_card)
        device.setContentsMargins(14, 10, 14, 12)
        device.setSpacing(8)

        row_title = QHBoxLayout()
        plug_icon = QLabel()
        plug_icon.setPixmap(QPixmap(str(core.bundle_root() / "assets/icons/plug.svg")).scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        st = QLabel("KẾT NỐI & NHẬN DIỆN MAIN")
        st.setObjectName("sectionTitle")
        row_title.addWidget(plug_icon)
        row_title.addWidget(st)
        row_title.addStretch(1)
        device.addLayout(row_title)

        conn = QHBoxLayout()
        conn.setSpacing(8)

        port_lbl = QLabel("Serial Port")
        port_lbl.setObjectName("portLabel")
        conn.addWidget(port_lbl)

        self.port = QComboBox()
        self.port.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        conn.addWidget(self.port, 1)

        self.scan_btn = QPushButton("QUÉT LẠI")
        self.scan_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/refresh.svg")))

        self.detect_btn = QPushButton("NHẬN DIỆN CHIP")
        self.detect_btn.setObjectName("primary")
        self.detect_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/chip_white.svg")))

        conn.addWidget(self.scan_btn)
        conn.addWidget(self.detect_btn)
        device.addLayout(conn)

        # 4 Metric Cards
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(10)
        metrics.setVerticalSpacing(0)
        self.chip_value = self.add_metric(metrics, 0, 0, "CHIP", "ESP32-S3", icon_name="chip.svg")
        self.mac_value = self.add_metric(metrics, 0, 1, "MAC", "80:B5:4E:61:1E:B0", icon_name="link.svg")
        self.fw_local_value = self.add_metric(metrics, 0, 2, "FIRMWARE LOCAL", "v1.0.0", icon_name="file.svg")
        self.fw_latest_value = self.add_metric(metrics, 0, 3, "FIRMWARE LATEST", "v1.0.0", icon_name="cloud.svg")
        device.addLayout(metrics)
        layout.addWidget(device_card)

        # ---------------- SECTION 2: FIRMWARE & UPDATE ----------------
        update_card = QFrame()
        update_card.setObjectName("card")
        update = QVBoxLayout(update_card)
        update.setContentsMargins(14, 10, 14, 12)
        update.setSpacing(8)

        update_header = QHBoxLayout()
        cloud_icon = QLabel()
        cloud_icon.setPixmap(QPixmap(str(core.bundle_root() / "assets/icons/cloud_plus.svg")).scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        ut = QLabel("FIRMWARE & UPDATE")
        ut.setObjectName("sectionTitle")
        update_header.addWidget(cloud_icon)
        update_header.addWidget(ut)
        update_header.addStretch(1)
        update.addLayout(update_header)

        update_buttons = QHBoxLayout()
        update_buttons.setSpacing(8)
        self.check_btn = QPushButton("KIỂM TRA PHIÊN BẢN")
        self.check_btn.setObjectName("secondary")
        self.check_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/search.svg")))

        self.sync_btn = QPushButton("TẢI / ĐỒNG BỘ FIRMWARE")
        self.sync_btn.setObjectName("secondary")
        self.sync_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/sync.svg")))

        self.gui_update_btn = QPushButton("NÂNG CẤP PHẦN MỀM")
        self.gui_update_btn.setObjectName("secondary")
        self.gui_update_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/download.svg")))

        self.check_btn.setToolTip("Kiểm tra manifest mới nhất trên GitHub, không tải hay ghi firmware.")
        self.sync_btn.setToolTip("Tải hoặc xác minh firmware đúng với chip đã nhận diện và kiểm tra SHA256.")
        self.gui_update_btn.setToolTip("Tải và nâng cấp chính ứng dụng khi có phiên bản GUI mới hơn.")

        self.sync_btn.setEnabled(False)
        self.gui_update_btn.setEnabled(False)

        update_buttons.addWidget(self.check_btn)
        update_buttons.addWidget(self.sync_btn)
        update_buttons.addWidget(self.gui_update_btn)
        update_buttons.addStretch(1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: #DDEAF3; background: #DDEAF3; width: 1px; max-width: 1px; margin: 2px 10px;")
        update_buttons.addWidget(sep2)

        self.update_status = QLabel(f"Stable • GUI latest v{APP_VERSION}")
        self.update_status.setObjectName("sectionHint")
        update_buttons.addWidget(self.update_status)
        update.addLayout(update_buttons)
        layout.addWidget(update_card)

        # ---------------- SECTION 3: FLASH & VERIFY ----------------
        flash_card = QFrame()
        flash_card.setObjectName("card")
        flash_layout = QVBoxLayout(flash_card)
        flash_layout.setContentsMargins(14, 10, 14, 12)
        flash_layout.setSpacing(6)

        fh = QHBoxLayout()
        ft = QVBoxLayout()
        ft.setSpacing(2)

        flash_title_row = QHBoxLayout()
        flash_title_row.setSpacing(6)
        bolt_icon = QLabel()
        bolt_icon.setPixmap(QPixmap(str(core.bundle_root() / "assets/icons/bolt.svg")).scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        flash_title = QLabel("NẠP & VERIFY FIRMWARE")
        flash_title.setObjectName("sectionTitle")
        flash_title_row.addWidget(bolt_icon)
        flash_title_row.addWidget(flash_title)
        flash_title_row.addStretch(1)
        ft.addLayout(flash_title_row)

        flash_hint = QLabel("Firmware được chọn tự động theo chip đã nhận diện. Không full-chip erase mặc định.")
        flash_hint.setObjectName("sectionHint")
        ft.addWidget(flash_hint)
        fh.addLayout(ft, 1)

        # Flash status label & pill + big flash button
        status_box = QHBoxLayout()
        status_box.setSpacing(8)
        status_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_lbl = QLabel("Trạng thái nạp:")
        status_lbl.setObjectName("sectionHint")
        self.flash_status = QLabel("CHƯA NẠP")
        self.flash_status.setObjectName("flashStatusPill")
        self.flash_status.setAlignment(Qt.AlignCenter)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setStyleSheet("color: #DDEAF3; background: #DDEAF3; width: 1px; max-width: 1px; margin: 2px 8px;")

        self.flash_btn = QPushButton("BẮT ĐẦU FLASH")
        self.flash_btn.setObjectName("flashBtn")
        self.flash_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/play.svg")))
        self.flash_btn.setEnabled(False)

        status_box.addWidget(status_lbl)
        status_box.addWidget(self.flash_status)
        status_box.addWidget(sep3)
        status_box.addWidget(self.flash_btn)
        fh.addLayout(status_box, 0)
        flash_layout.addLayout(fh)

        # Real Progress Bar (HIDDEN until flash is active)
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        flash_layout.addWidget(self.progress)
        layout.addWidget(flash_card)

        # ---------------- SECTION 4: TECHNICAL LOG ----------------
        log_card = QFrame()
        log_card.setObjectName("card")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(14, 10, 14, 12)
        log_layout.setSpacing(6)

        log_header = QHBoxLayout()
        log_icon = QLabel()
        log_icon.setPixmap(QPixmap(str(core.bundle_root() / "assets/icons/log.svg")).scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lt = QLabel("EVENT / TECHNICAL LOG")
        lt.setObjectName("sectionTitle")
        log_header.addWidget(log_icon)
        log_header.addWidget(lt)
        log_header.addStretch(1)

        self.clear_log_btn = QPushButton("XÓA LOG")
        self.clear_log_btn.setObjectName("secondarySmall")
        self.clear_log_btn.setIcon(QIcon(str(core.bundle_root() / "assets/icons/trash.svg")))
        self.clear_log_btn.clicked.connect(self.log_clear)
        log_header.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_header)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Detect / sync / flash / verify log sẽ hiển thị tại đây…")
        log_layout.addWidget(self.log, 1)
        layout.addWidget(log_card, 1)

        # Connections
        self.scan_btn.clicked.connect(self.refresh_ports)
        self.detect_btn.clicked.connect(self.detect)
        self.check_btn.clicked.connect(self.check_updates)
        self.sync_btn.clicked.connect(self.sync_firmware)
        self.gui_update_btn.clicked.connect(self.update_gui)
        self.flash_btn.clicked.connect(self.flash)

        self.init_startup_state()

    def add_metric(self, grid, row, col, name, initial, icon_name=None):
        card = QFrame()
        card.setObjectName("metricCard")
        box = QHBoxLayout(card)
        box.setContentsMargins(14, 10, 14, 10)
        box.setSpacing(12)

        if icon_name:
            icon_path = core.bundle_root() / "assets" / "icons" / icon_name
            if icon_path.exists():
                icon_lbl = QLabel()
                icon_lbl.setPixmap(QPixmap(str(icon_path)).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_lbl.setAlignment(Qt.AlignCenter)
                box.addWidget(icon_lbl, 0, Qt.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        k = QLabel(name)
        k.setObjectName("metric")
        k.setAlignment(Qt.AlignCenter)
        v = QLabel(initial)
        v.setObjectName("value")
        v.setAlignment(Qt.AlignCenter)
        v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_col.addWidget(k)
        text_col.addWidget(v)
        box.addLayout(text_col, 1)

        grid.addWidget(card, row, col)
        return v

    def append_log(self, s, color=None, bold=False):
        if not s:
            return
        now = datetime.datetime.now().strftime("%H:%M:%S")
        for line in str(s).splitlines():
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("["):
                ts_part = line[:10]
                msg_part = line[10:]
            else:
                ts_part = f"[{now}]"
                msg_part = f"  {line}"

            safe_msg = html.escape(msg_part)
            if color:
                w_style = f"font-weight: 700;" if bold else ""
                html_line = f'<span style="color: #6E879C;">{ts_part}</span><span style="color: {color}; {w_style}">{safe_msg}</span>'
            elif "CHIP:" in line and "MAC:" in line:
                html_line = f'<span style="color: #6E879C;">{ts_part}</span><span style="color: #18A957; font-weight: 700;">{safe_msg}</span>'
            elif "FLASH PASS" in line or "THÀNH CÔNG" in line:
                html_line = f'<span style="color: #6E879C;">{ts_part}</span><span style="color: #18A957; font-weight: 700;">{safe_msg}</span>'
            elif "FAIL" in line or "Error" in line or "error" in line:
                html_line = f'<span style="color: #6E879C;">{ts_part}</span><span style="color: #E43C48; font-weight: 700;">{safe_msg}</span>'
            else:
                html_line = f'<span style="color: #6E879C;">{ts_part}</span><span style="color: #1B3650;">{safe_msg}</span>'

            self.log.append(html_line)

    def log_clear(self):
        self.log.clear()

    def set_state_pill(self, text, pill_type="ready"):
        if pill_type == "ready" or "PASS" in text or "READY" in text:
            self.state_label.setStyleSheet("background: #EAF8EF; color: #18A957; border: 1px solid #BAEBD0; border-radius: 12px; padding: 3px 11px; font-size: 11px; font-weight: 800;")
        elif pill_type == "fail" or "FAIL" in text:
            self.state_label.setStyleSheet("background: #FDE8E9; color: #E43C48; border: 1px solid #F8B8BB; border-radius: 12px; padding: 3px 11px; font-size: 11px; font-weight: 800;")
        else:
            self.state_label.setStyleSheet("background: #EAF4FC; color: #1688D4; border: 1px solid #C8E1F4; border-radius: 12px; padding: 3px 11px; font-size: 11px; font-weight: 800;")

        bullet = "● " if not (text.startswith("●") or text.startswith("✓") or text.startswith("✕")) else ""
        self.state_label.setText(f"{bullet}{text}")

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
            self.set_state_pill(text, pill_type="busy" if busy else "ready")

    def _refresh_button_states(self):
        self.flash_btn.setEnabled(self.detected_chip is not None)
        self.sync_btn.setEnabled(self.detected_chip is not None)
        try:
            self.gui_update_btn.setEnabled(core.gui_update_available(APP_VERSION, self.remote_manifest))
        except Exception:
            self.gui_update_btn.setEnabled(False)

    def init_startup_state(self):
        self.port.clear()
        ports = core.list_serial_ports()
        for dev, details in ports:
            self.port.addItem(f"{dev}   {details}".rstrip(), dev)

        # Log lines matching reference format
        self.append_log(f"T500 ESP32 Flasher v{APP_VERSION}  -  AUBOT")
        self.append_log("Scanning serial ports...")
        for dev, details in ports:
            self.append_log(f"Found device: {dev}  ({details})")
        self.append_log("Device ready. Waiting for user action.")
        self.check_updates(silent=True)

    def refresh_ports(self):
        current = self.port.currentData()
        self.port.clear()
        ports = core.list_serial_ports()
        for dev, details in ports:
            self.port.addItem(f"{dev}   {details}".rstrip(), dev)
        if current:
            idx = self.port.findData(current)
            if idx >= 0:
                self.port.setCurrentIndex(idx)
        self.append_log("Scanning serial ports...")
        for dev, details in ports:
            self.append_log(f"Found device: {dev}  ({details})")

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
        self.set_state_pill(text, pill_type="busy")
        if text.startswith("FLASHING"):
            pct = int((cur * 100) / total) if total else 0
            self.flash_status.setText(f"ĐANG NẠP • {pct}%")

    def silent_job_error(self, tb):
        pass

    def job_error(self, tb):
        self.append_log(tb, color="#E43C48")
        was_flashing = "FLASHING" in self.state_label.text()
        self.set_busy(False, "FAIL")
        self.set_state_pill("FAIL", pill_type="fail")
        if was_flashing:
            self.flash_status.setText("FLASH FAIL")
            self.flash_status.setStyleSheet("background: #FDE8E9; color: #E43C48; border: 1px solid #F8B8BB; border-radius: 10px; padding: 4px 12px; font-size: 11px; font-weight: 800;")
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

        self.append_log("Detecting chip information...")

        def work(sig):
            return core.detect_chip(port)

        self.start_job(work, self.detect_done, "DETECTING")

    def detect_done(self, result):
        chip, mac, out = result
        self.append_log(out)
        if chip not in ("ESP32", "ESP32-S3"):
            self.detected_chip = None
            self.chip_value.setText("Không hỗ trợ")
            self.set_state_pill("DETECT FAIL", pill_type="fail")
            return

        self.detected_chip = chip
        self.detected_mac = mac

        match = re.search(r"Chip is (ESP32[^\n\r(]+(\([^)]+\))?)", out)
        chip_display = match.group(1).strip() if match else chip
        self.chip_value.setText(chip)
        self.mac_value.setText(mac)
        self.update_fw_labels()
        self.set_state_pill("READY", pill_type="ready")
        self.append_log(f"CHIP: {chip_display}  •  MAC: {mac}", color="#18A957", bold=True)
        self.append_log(f"Firmware local: {self.fw_local_value.text()}  |  Firmware latest: {self.fw_latest_value.text()}")
        self.append_log("Device ready. Waiting for user action.")
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
                (" • có bản GUI mới" if gui_new else "")
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
            self.set_state_pill("READY", pill_type="ready")
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
            self.set_state_pill("FLASH PASS", pill_type="ready")
            self.flash_status.setText("THÀNH CÔNG • 100%")
            self.flash_status.setStyleSheet("background: #EAF8EF; color: #18A957; border: 1px solid #BAEBD0; border-radius: 10px; padding: 4px 12px; font-size: 11px; font-weight: 800;")
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
