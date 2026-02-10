import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.desktop.api import DesktopController
from app.desktop.ui_helpers import open_in_file_manager, open_parent_folder, pretty_json


class DesktopMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.controller = DesktopController()
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._on_idle_tick)
        self.last_audio_path = ''
        self.last_process_time = '-'

        self.setWindowTitle('数字人操作平台 - Desktop App + Simple UI')
        self.resize(1180, 760)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addWidget(self._build_status_bar())
        root.addWidget(self._build_comment_group())
        root.addWidget(self._build_idle_group())
        root.addWidget(self._build_tabs(), 1)

        self._refresh_event_tab()
        self._refresh_status_labels()

    def _build_status_bar(self) -> QWidget:
        box = QGroupBox('连接/状态')
        row = QHBoxLayout(box)

        self.mode_label = QLabel()
        self.idle_state_label = QLabel('Idle: Off')
        self.last_time_label = QLabel('最近处理时间: -')

        self.open_output_btn = QPushButton('打开输出目录')
        self.open_output_btn.clicked.connect(self._open_output_dirs)

        self.clear_log_btn = QPushButton('清空界面日志')
        self.clear_log_btn.clicked.connect(self._clear_ui_logs)

        row.addWidget(self.mode_label)
        row.addStretch()
        row.addWidget(self.idle_state_label)
        row.addSpacing(16)
        row.addWidget(self.last_time_label)
        row.addStretch()
        row.addWidget(self.open_output_btn)
        row.addWidget(self.clear_log_btn)
        return box

    def _build_comment_group(self) -> QWidget:
        box = QGroupBox('评论输入')
        layout = QHBoxLayout(box)

        form = QFormLayout()
        self.user_input = QLineEdit('u1')
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText('输入评论后回车或点击发送')
        self.text_input.returnPressed.connect(self._send_comment)

        form.addRow('user_id', self.user_input)
        form.addRow('评论文本', self.text_input)

        btn_col = QVBoxLayout()
        self.send_btn = QPushButton('发送')
        self.send_btn.clicked.connect(self._send_comment)
        btn_col.addWidget(self.send_btn)

        quick_row = QHBoxLayout()
        for text in ['问价格', '问功能', '你好']:
            b = QPushButton(text)
            b.clicked.connect(lambda _, t=text: self._quick_send(t))
            quick_row.addWidget(b)
        btn_col.addLayout(quick_row)
        btn_col.addStretch()

        layout.addLayout(form, 2)
        layout.addLayout(btn_col, 3)
        return box

    def _build_idle_group(self) -> QWidget:
        box = QGroupBox('Idle 控制')
        row = QHBoxLayout(box)

        self.idle_toggle = QCheckBox('Idle On/Off')
        self.idle_toggle.stateChanged.connect(self._toggle_idle)

        self.idle_interval = QSpinBox()
        self.idle_interval.setRange(1, 600)
        self.idle_interval.setValue(int(self.controller.settings.idle_interval_seconds))
        self.idle_interval.setSuffix(' 秒')

        self.idle_preview = QLabel('idle 预览: -')
        if self.controller.state_machine._scripts.idle_lines:  # noqa: SLF001
            preview = self.controller.state_machine._scripts.idle_lines[0]  # noqa: SLF001
            self.idle_preview.setText(f'idle 预览: 1/{len(self.controller.state_machine._scripts.idle_lines)} {preview}')  # noqa: SLF001

        self.play_latest_btn = QPushButton('播放最新 wav')
        self.play_latest_btn.clicked.connect(self._play_latest_wav)

        self.open_latest_btn = QPushButton('打开最新 wav 所在位置')
        self.open_latest_btn.clicked.connect(self._open_latest_wav_folder)

        row.addWidget(self.idle_toggle)
        row.addWidget(QLabel('间隔'))
        row.addWidget(self.idle_interval)
        row.addWidget(self.idle_preview, 1)
        row.addWidget(self.play_latest_btn)
        row.addWidget(self.open_latest_btn)
        return box

    def _build_tabs(self) -> QWidget:
        tabs = QTabWidget()

        log_tab = QWidget()
        log_layout = QHBoxLayout(log_tab)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.log_table = QTableWidget(0, 7)
        self.log_table.setHorizontalHeaderLabels(['时间', 'user_id', 'text', 'category', 'dedup', 'ratelimit', 'reply'])
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.itemSelectionChanged.connect(self._show_log_detail)
        self.log_table.horizontalHeader().setStretchLastSection(True)

        self.log_detail = QTextEdit()
        self.log_detail.setReadOnly(True)
        self.log_detail.setPlaceholderText('点击左侧日志行查看详细信息')

        splitter.addWidget(self.log_table)
        splitter.addWidget(self.log_detail)
        splitter.setSizes([760, 380])

        log_layout.addWidget(splitter)
        tabs.addTab(log_tab, 'Log')

        event_tab = QWidget()
        event_layout = QVBoxLayout(event_tab)
        event_top = QHBoxLayout()
        self.event_refresh_btn = QPushButton('刷新')
        self.event_refresh_btn.clicked.connect(self._refresh_event_tab)
        event_top.addWidget(self.event_refresh_btn)
        event_top.addStretch()

        self.event_text = QTextEdit()
        self.event_text.setReadOnly(True)

        event_layout.addLayout(event_top)
        event_layout.addWidget(self.event_text)
        tabs.addTab(event_tab, 'Event')

        return tabs

    def _send_comment(self) -> None:
        user_id = self.user_input.text().strip() or 'u1'
        text = self.text_input.text().strip()
        if not text:
            QMessageBox.information(self, '提示', '请输入评论文本。')
            return

        result = self.controller.process_comment(user_id=user_id, text=text)
        self._on_new_result(result, user_id, text)
        self.text_input.clear()

    def _quick_send(self, tag: str) -> None:
        mapping = {'问价格': '这个多少钱？', '问功能': '这个有哪些功能？', '你好': '你好'}
        self.text_input.setText(mapping.get(tag, tag))
        self._send_comment()

    def _toggle_idle(self) -> None:
        if self.idle_toggle.isChecked():
            ms = int(self.idle_interval.value() * 1000)
            self.idle_timer.start(max(ms, 300))
            self.idle_state_label.setText('Idle: On')
        else:
            self.idle_timer.stop()
            self.idle_state_label.setText('Idle: Off')

    def _on_idle_tick(self) -> None:
        result = self.controller.generate_idle_line()
        if result.get('audio_path'):
            self._on_new_result(result, user_id='[idle]', text='(idle_line)')

    def _on_new_result(self, result: dict, user_id: str, text: str) -> None:
        self.last_process_time = time.strftime('%H:%M:%S')
        self.last_audio_path = result.get('audio_path') or self.last_audio_path
        self._append_log_row(
            user_id=user_id,
            text=text,
            category=result.get('category', ''),
            dedup_hit=result.get('dedup_hit', False),
            ratelimit_hit=result.get('ratelimit_hit', False),
            reply_text=result.get('reply_text', ''),
            detail=result,
        )
        self._refresh_event_tab()
        self._refresh_status_labels()

    def _append_log_row(self, *, user_id: str, text: str, category: str, dedup_hit: bool, ratelimit_hit: bool, reply_text: str, detail: dict) -> None:
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        vals = [
            time.strftime('%H:%M:%S'),
            user_id,
            text,
            category,
            str(dedup_hit),
            str(ratelimit_hit),
            reply_text,
        ]
        for col, val in enumerate(vals):
            item = QTableWidgetItem(val)
            if col == 6:
                item.setToolTip(val)
            self.log_table.setItem(row, col, item)

        self.log_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, detail)
        self.log_table.scrollToBottom()

    def _show_log_detail(self) -> None:
        items = self.log_table.selectedItems()
        if not items:
            return
        row = items[0].row()
        data = self.log_table.item(row, 0).data(Qt.ItemDataRole.UserRole) or {}
        event_json = data.get('event_json', {})
        detail = {
            'reply_text': data.get('reply_text', ''),
            'audio_path': data.get('audio_path', ''),
            'event_id': event_json.get('event_id', ''),
            'meta': event_json.get('meta', {}),
            'raw_result': data,
        }
        self.log_detail.setPlainText(pretty_json(detail))

    def _refresh_event_tab(self) -> None:
        event_json = self.controller.get_event_json()
        self.event_text.setPlainText(pretty_json(event_json))

    def _refresh_status_labels(self) -> None:
        self.mode_label.setText(f'模式: {self.controller.mode}')
        self.last_time_label.setText(f'最近处理时间: {self.last_process_time}')

    def _open_output_dirs(self) -> None:
        try:
            open_in_file_manager(self.controller.settings.audio_dir)
            open_in_file_manager(self.controller.settings.events_dir)
        except Exception as exc:
            QMessageBox.warning(self, '提示', f'无法打开目录: {exc}')

    def _clear_ui_logs(self) -> None:
        self.log_table.setRowCount(0)
        self.log_detail.clear()

    def _play_latest_wav(self) -> None:
        if not self.last_audio_path:
            QMessageBox.information(self, '提示', '暂无可播放音频。')
            return
        p = Path(self.last_audio_path)
        if not p.exists():
            QMessageBox.warning(self, '提示', f'文件不存在: {p}')
            return
        if os.name == 'nt':
            import winsound

            winsound.PlaySound(str(p), winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        QMessageBox.information(self, '提示', f'当前系统不支持 winsound 自动播放，请手动打开: {p}')

    def _open_latest_wav_folder(self) -> None:
        if not self.last_audio_path:
            QMessageBox.information(self, '提示', '暂无最新 wav。')
            return
        try:
            open_parent_folder(self.last_audio_path)
        except Exception as exc:
            QMessageBox.warning(self, '提示', f'无法打开路径: {exc}')


def main() -> None:
    app = QApplication(sys.argv)
    window = DesktopMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
