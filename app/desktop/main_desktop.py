import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
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
from app.integrations.input_adapter import from_file_line, read_appended_lines

logger = logging.getLogger(__name__)


class DesktopMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.controller = DesktopController()
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._on_idle_tick)
        self.file_timer = QTimer(self)
        self.file_timer.timeout.connect(self._poll_input_file)
        self.file_offset = 0
        self.file_path = Path('output/input_comments.txt')

        self.last_audio_path = ''
        self.last_process_time = '-'

        self.setWindowTitle('数字人操作平台 - Desktop App + Simple UI')
        self.resize(1200, 980)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addWidget(self._build_status_bar())
        root.addWidget(self._build_provider_group())
        root.addWidget(self._build_obs_group())
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

    def _build_provider_group(self) -> QWidget:
        box = QGroupBox('Provider 选择（阶段C）')
        layout = QHBoxLayout(box)

        form = QFormLayout()
        self.llm_provider = QComboBox()
        self.llm_provider.addItems(['mock', 'openai'])
        self.llm_model = QLineEdit('gpt-4o-mini')
        self.llm_key = QLineEdit('')
        self.llm_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.llm_timeout = QSpinBox()
        self.llm_timeout.setRange(1, 120)
        self.llm_timeout.setValue(10)

        self.tts_provider = QComboBox()
        self.tts_provider.addItems(['silent', 'openai'])
        self.tts_model = QLineEdit('gpt-4o-mini-tts')
        self.tts_voice = QLineEdit('alloy')
        self.tts_key = QLineEdit('')
        self.tts_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.tts_timeout = QSpinBox()
        self.tts_timeout.setRange(1, 120)
        self.tts_timeout.setValue(10)

        form.addRow('LLM Provider', self.llm_provider)
        form.addRow('LLM Model', self.llm_model)
        form.addRow('LLM Key', self.llm_key)
        form.addRow('LLM Timeout', self.llm_timeout)
        form.addRow('TTS Provider', self.tts_provider)
        form.addRow('TTS Model', self.tts_model)
        form.addRow('TTS Voice', self.tts_voice)
        form.addRow('TTS Key', self.tts_key)
        form.addRow('TTS Timeout', self.tts_timeout)

        side = QVBoxLayout()
        self.apply_provider_btn = QPushButton('应用 Provider 配置')
        self.apply_provider_btn.clicked.connect(self._apply_provider_config)
        self.provider_status_label = QLabel('Provider状态: LLM=mock, TTS=silent_wav')

        side.addWidget(self.apply_provider_btn)
        side.addWidget(self.provider_status_label)
        side.addStretch()

        layout.addLayout(form, 3)
        layout.addLayout(side, 2)
        return box

    def _build_obs_group(self) -> QWidget:
        box = QGroupBox('OBS 输出器（阶段A）')
        layout = QHBoxLayout(box)

        form = QFormLayout()
        self.obs_enable = QCheckBox('启用OBS自动推送')
        self.obs_enable.setChecked(False)
        self.obs_host = QLineEdit('127.0.0.1')
        self.obs_port = QSpinBox()
        self.obs_port.setRange(1, 65535)
        self.obs_port.setValue(4455)
        self.obs_password = QLineEdit('')
        self.obs_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.obs_subtitle_source = QLineEdit('字幕')
        self.obs_audio_source = QLineEdit('TTS音频')

        form.addRow('启用', self.obs_enable)
        form.addRow('Host', self.obs_host)
        form.addRow('Port', self.obs_port)
        form.addRow('Password', self.obs_password)
        form.addRow('字幕源名称', self.obs_subtitle_source)
        form.addRow('音频源名称', self.obs_audio_source)

        btns = QVBoxLayout()
        self.obs_connect_btn = QPushButton('连接 OBS')
        self.obs_connect_btn.clicked.connect(self._connect_obs)
        self.obs_test_btn = QPushButton('测试推送')
        self.obs_test_btn.clicked.connect(self._test_obs)
        self.obs_status_label = QLabel('OBS状态: 未连接')

        btns.addWidget(self.obs_connect_btn)
        btns.addWidget(self.obs_test_btn)
        btns.addWidget(self.obs_status_label)
        btns.addStretch()

        layout.addLayout(form, 3)
        layout.addLayout(btns, 2)
        return box

    def _build_comment_group(self) -> QWidget:
        box = QGroupBox('评论输入适配层（阶段B）')
        layout = QVBoxLayout(box)

        top = QHBoxLayout()
        form = QFormLayout()
        self.user_input = QLineEdit('u1')
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText('输入评论后回车或点击发送')
        self.text_input.returnPressed.connect(self._send_comment)

        self.input_mode = QComboBox()
        self.input_mode.addItems(['manual_ui', 'http_post_/comment', 'file_tail'])
        self.input_mode.currentTextChanged.connect(self._on_input_mode_changed)
        self.input_mode_status = QLabel('输入方式状态: manual_ui')

        form.addRow('user_id', self.user_input)
        form.addRow('评论文本', self.text_input)
        form.addRow('输入方式', self.input_mode)

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
        btn_col.addWidget(self.input_mode_status)
        btn_col.addStretch()

        top.addLayout(form, 2)
        top.addLayout(btn_col, 3)

        file_row = QHBoxLayout()
        self.file_input_path = QLineEdit(str(self.file_path))
        self.file_watch_btn = QPushButton('启动文件监听')
        self.file_watch_btn.clicked.connect(self._toggle_file_watch)
        self.file_watch_status = QLabel('文件监听: Off')
        file_row.addWidget(QLabel('监听文件'))
        file_row.addWidget(self.file_input_path, 1)
        file_row.addWidget(self.file_watch_btn)
        file_row.addWidget(self.file_watch_status)

        layout.addLayout(top)
        layout.addLayout(file_row)
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

    def _apply_provider_config(self) -> None:
        try:
            self.controller.set_provider_config(
                llm_provider=self.llm_provider.currentText(),
                llm_api_key=self.llm_key.text().strip(),
                llm_model=self.llm_model.text().strip() or 'gpt-4o-mini',
                llm_timeout=int(self.llm_timeout.value()),
                tts_provider=self.tts_provider.currentText(),
                tts_api_key=self.tts_key.text().strip(),
                tts_model=self.tts_model.text().strip() or 'gpt-4o-mini-tts',
                tts_voice=self.tts_voice.text().strip() or 'alloy',
                tts_timeout=int(self.tts_timeout.value()),
            )
            status = self.controller.get_provider_status()
            self.provider_status_label.setText(f'Provider状态: {status}')
            QMessageBox.information(self, 'Provider', 'Provider 配置已应用（失败会自动回退 Mock/Silent）')
        except Exception as exc:
            logger.exception('apply provider config failed: %s', exc)
            QMessageBox.warning(self, 'Provider', f'配置失败: {exc}')

    def _on_input_mode_changed(self, mode: str) -> None:
        self.input_mode_status.setText(f'输入方式状态: {mode}')

    def _toggle_file_watch(self) -> None:
        if self.file_timer.isActive():
            self.file_timer.stop()
            self.file_watch_btn.setText('启动文件监听')
            self.file_watch_status.setText('文件监听: Off')
            return

        try:
            self.file_path = Path(self.file_input_path.text().strip() or 'output/input_comments.txt')
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self.file_path.touch()
            self.file_offset = self.file_path.stat().st_size
            self.file_timer.start(500)
            self.file_watch_btn.setText('停止文件监听')
            self.file_watch_status.setText(f'文件监听: On ({self.file_path})')
        except Exception as exc:
            logger.exception('Start file watch failed: %s', exc)
            QMessageBox.warning(self, '文件监听', f'启动失败: {exc}')

    def _poll_input_file(self) -> None:
        try:
            lines, self.file_offset = read_appended_lines(self.file_path, self.file_offset)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    comment = from_file_line(line)
                    result = self.controller.process_external_comment(comment)
                    self._on_new_result(result, user_id=comment.user_id, text=comment.text)
                except Exception as parse_exc:
                    logger.exception('Parse/process input file line failed: %s', parse_exc)
                    self.file_watch_status.setText(f'文件监听: 行处理失败 ({parse_exc})')
        except Exception as exc:
            logger.exception('Polling input file failed: %s', exc)
            self.file_watch_status.setText(f'文件监听异常: {exc}')

    def _apply_obs_config(self) -> None:
        self.controller.set_obs_config(
            host=self.obs_host.text().strip() or '127.0.0.1',
            port=int(self.obs_port.value()),
            password=self.obs_password.text(),
            subtitle_source=self.obs_subtitle_source.text().strip(),
            audio_source=self.obs_audio_source.text().strip(),
            enabled=self.obs_enable.isChecked(),
        )

    def _connect_obs(self) -> None:
        try:
            self._apply_obs_config()
            ok, msg = self.controller.connect_obs()
            self.obs_status_label.setText(f'OBS状态: {msg}')
            if ok:
                QMessageBox.information(self, 'OBS', msg)
            else:
                QMessageBox.warning(self, 'OBS', msg)
        except Exception as exc:
            logger.exception('OBS connect ui failed: %s', exc)
            QMessageBox.critical(self, 'OBS', f'OBS连接异常: {exc}')

    def _test_obs(self) -> None:
        try:
            self._apply_obs_config()
            ok, msg = self.controller.test_obs()
            if ok:
                event_json = self.controller.get_event_json()
                reply_text = event_json.get('text', 'OBS测试字幕')
                audio_path = event_json.get('audio_path', '')
                push_ok, push_msg = self.controller.obs.push_event(reply_text, audio_path)
                final_msg = f'{msg}\n推送结果: {push_msg}'
                self.obs_status_label.setText(f'OBS状态: {final_msg}')
                if push_ok:
                    QMessageBox.information(self, 'OBS测试', final_msg)
                else:
                    QMessageBox.warning(self, 'OBS测试', final_msg)
            else:
                self.obs_status_label.setText(f'OBS状态: {msg}')
                QMessageBox.warning(self, 'OBS测试', msg)
        except Exception as exc:
            logger.exception('OBS test ui failed: %s', exc)
            QMessageBox.critical(self, 'OBS测试', f'OBS测试异常: {exc}')

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
        obs_result = result.get('obs_result', '')
        if obs_result:
            self.obs_status_label.setText(f'OBS状态: {obs_result}')

        provider_status = result.get('provider_status', {})
        if provider_status:
            self.provider_status_label.setText(f'Provider状态: {provider_status}')

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
            'msg_id': data.get('msg_id'),
            'obs_result': data.get('obs_result', ''),
            'provider_status': data.get('provider_status', {}),
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
            logger.exception('Open output dirs failed: %s', exc)
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
            logger.exception('Open latest wav folder failed: %s', exc)
            QMessageBox.warning(self, '提示', f'无法打开路径: {exc}')


def run_selfcheck() -> int:
    """Minimal runtime smoke check for packaged EXE/CI."""
    try:
        controller = DesktopController()
        # quick dry-run path: build one idle event with existing pipeline
        result = controller.generate_idle_line()
        event_json = result.get('event_json', {})
        if not isinstance(event_json, dict):
            raise RuntimeError('invalid event json')
        return 0
    except Exception as exc:
        logger.exception('selfcheck failed: %s', exc)
        return 1


def print_help() -> None:
    print('NewAIHuman Desktop')
    print('  --help      show help')
    print('  --selfcheck run non-GUI smoke check and exit')


def main() -> None:
    args = set(sys.argv[1:])
    if '--help' in args or '-h' in args:
        print_help()
        sys.exit(0)
    if '--selfcheck' in args:
        sys.exit(run_selfcheck())

    app = QApplication(sys.argv)
    window = DesktopMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
