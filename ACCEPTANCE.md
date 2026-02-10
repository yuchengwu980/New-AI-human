# ACCEPTANCE（在现有框架上增量升级）

> 目标：在**不改变现有架构/入口/输出协议/打包方式**前提下，做后续增强时的统一验收清单。

## 0. 强约束回归（必须全部满足）

- [ ] 保留桌面入口：`python -m app.desktop.main_desktop` 可启动窗口。
- [ ] 保留 Web 入口：`python -m app.main` 或 `uvicorn app.main:app` 可启动。
- [ ] 不替换技术栈：桌面仍为 PySide6，后端仍为 FastAPI。
- [ ] 不破坏输出协议：继续写入
  - `output/events/last_event.json`（覆盖）
  - `output/events/history_YYYYMMDD.jsonl`（追加）
  - `output/audio/*.wav`
- [ ] 不删除现有打包链路：`build_win.bat`、PyInstaller 参数、`.github/workflows/build-windows.yml` 保留。

---

## 1. 现有关键模块/入口/数据流（基线确认）

### 1.1 关键入口

- [ ] FastAPI 入口：`app/main.py`
  - `GET /health`
  - `POST /api/mock/push`
  - `GET /api/ui/state`
  - `GET /ui`
- [ ] 桌面入口：`app/desktop/main_desktop.py`
- [ ] 桌面本地调用封装：`app/desktop/api.py`
- [ ] 打包入口脚本：`build_win.bat`

### 1.2 现有数据流（必须延续）

- [ ] 评论输入（Web 或 Desktop）
- [ ] `pipeline/orchestrator.py`：去重 -> 限频 -> 分类 -> 状态机 -> TTS -> 写事件
- [ ] `outputs/writer.py`：事件落盘到 last_event + history
- [ ] `tts/silent_wav.py`：生成可播放占位 wav

### 1.3 资源/运行时路径（打包兼容）

- [ ] `app/utils/paths.py` 的 `resource_path()` 能在源码与 PyInstaller 环境读到 scripts。
- [ ] `app/config.py` 的 runtime path 逻辑确保打包后输出写到 exe 同级 `output/`。
- [ ] `app/dialogue/scripts.py` 能加载：
  - `scripts/idle_lines_zh.txt`
  - `scripts/reply_templates_zh.txt`

---

## 2. 行为验收（桌面版）

### 2.1 评论处理主链路

- [ ] 打开桌面窗口后，输入 `user_id=u1`、`text=你好`，点击发送。
- [ ] UI 日志新增一条记录（含 category / dedup_hit / ratelimit_hit / reply_text）。
- [ ] Event 页签可看到格式化 JSON（包含 `event_id/type/text/audio_path/meta`）。
- [ ] 文件系统有新输出：
  - `output/events/last_event.json` 更新
  - `output/events/history_YYYYMMDD.jsonl` 追加
  - `output/audio/*.wav` 新文件

### 2.2 去重与限频

- [ ] 60s 内重复发送同一 `user_id+text`，命中去重（`dedup_hit=true`）。
- [ ] 高频发送同一用户，命中用户限频（`ratelimit_hit=true`）。
- [ ] 全局高频发送，命中全局限频（仍不崩溃）。

### 2.3 Idle 行为

- [ ] 开启 Idle 开关后，按设定间隔自动触发 idle_line。
- [ ] 关闭 Idle 开关后，停止自动触发。
- [ ] idle_line 也会写事件 JSON 与 wav 文件。

### 2.4 桌面辅助功能

- [ ] “打开输出目录”可打开 `output/audio` 与 `output/events`。
- [ ] “清空界面日志”仅清 UI，不删除磁盘文件。
- [ ] “播放最新 wav”在 Windows 可用（不可用时有清晰提示）。

---

## 3. 行为验收（Web 兼容性）

- [ ] `/ui` 可访问（200），并可发送 mock 评论。
- [ ] `/api/ui/state` 返回 `recent` 与 `last_event`（若无则空结构）。
- [ ] 切换 `PLATFORM_API_ENABLED=false` 时系统正常。
- [ ] `PLATFORM_API_ENABLED=true` 但缺配置时，仅记录错误日志，不导致主服务崩溃。

---

## 4. 打包验收（Windows 下载即用）

### 4.1 构建产物

- [ ] 执行 `build_win.bat` 成功。
- [ ] 产物存在：`dist/NewAIHuman/NewAIHuman.exe`。
- [ ] 产物压缩包存在：`NewAIHuman_Win64.zip`。
- [ ] zip 中包含：
  - `NewAIHuman.exe`
  - `scripts/`（或已被打进 exe 且可读取）
  - `output/audio`、`output/events` 目录
  - `README_使用说明.txt`

### 4.2 干净机运行

- [ ] 在无 Python 环境的 Windows 机器，解压并双击 exe 可启动。
- [ ] 输入“你好”可生成 `last_event.json` 与 `wav`。
- [ ] scripts 话术非空可加载。

### 4.3 CI（若启用）

- [ ] `workflow_dispatch` 可触发 Windows 打包。
- [ ] `v*` tag push 可触发打包并上传 artifact。

---

## 5. 回归命令（建议每次增量升级都跑）

```bash
pytest -q tests/test_dedup.py tests/test_ratelimit.py tests/test_state_machine.py
python -m py_compile $(rg --files app tests -g '*.py' | tr '\n' ' ')
```

> 若环境允许依赖完整安装，再补跑桌面/UI测试与打包验证。
