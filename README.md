# 数字人操作平台（控制器）MVP

这是一个可本地运行的最小 MVP：把评论输入（Mock 或真实平台 API 适配器）接入后端流水线，经过**去重/限频/分类**，进入**话术状态机**，生成可播放的 **wav**（默认静音占位），并输出给渲染层可消费的事件 JSON。

## 1. 项目结构

```text
app/
  main.py
  config.py
  models.py
  sources/
    base.py
    mock_source.py
    platform_api.py
  pipeline/
    dedup.py
    ratelimit.py
    classify.py
    orchestrator.py
  dialogue/
    state_machine.py
    scripts.py
  tts/
    base.py
    silent_wav.py
  outputs/
    writer.py
  ui/
    static/
    templates/index.html
scripts/
  idle_lines_zh.txt
  reply_templates_zh.txt
output/
  audio/
  events/
tests/
requirements.txt
.env.example
run.bat
```

## 2. 安装与启动（Windows 命令行）

> 默认使用 Mock 评论源，离线可运行。

### 2.1 手动启动（推荐先走一遍）

```bat
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

也可使用：

```bat
.venv\Scripts\python -m app.main
```

启动后访问：
- Health: `http://127.0.0.1:8000/health`
- 控制台 UI: `http://127.0.0.1:8000/ui`

### 2.2 一键启动（小白友好）

```bat
run.bat
```

脚本会自动：
1. 创建 `.venv`（若不存在）
2. 安装 `requirements.txt`
3. 自动复制 `.env.example -> .env`（若不存在）
4. 启动服务并打印 `/health` 与 `/ui` 地址

### 2.3 安装失败（网络/代理）

如果 `pip install` 因网络导致失败，可选以下方式：

1) 临时指定镜像：

```bat
.venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2) 设置 `PIP_INDEX_URL` 后再安装：

```bat
set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
.venv\Scripts\python -m pip install -r requirements.txt
```


## 2.4 桌面版（无需浏览器）

运行以下命令（或直接双击 `run_desktop.bat`）：

```bat
run_desktop.bat
```

手动启动方式：

```bat
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m app.desktop.main_desktop
```

桌面窗口说明（全部在一个应用窗口完成）：
- 顶部状态栏：显示当前模式（Mock/PlatformApi 占位）、Idle 状态、最近处理时间
- 顶部按钮：打开输出目录、清空界面日志
- 评论输入区：`user_id`（默认 u1）+ 评论文本（支持回车发送）+ 发送按钮
- 快捷按钮：`问价格` / `问功能` / `你好`（快速测试分类）
- Idle 控制区：Idle 开关、间隔秒数（默认 8 秒）、idle 预览
- 下半 Tab：
  - `Log`：表格日志（时间、user_id、text、category、dedup_hit、ratelimit_hit、reply_text），点击行看详情（reply/audio/event_id/meta）
  - `Event`：`last_event.json` 格式化显示，支持手动刷新
- 音频按钮：播放最新 wav（Windows 用 winsound）、打开最新 wav 所在目录

输出文件位置：
- `output/audio/*.wav`
- `output/events/last_event.json`
- `output/events/history_YYYYMMDD.jsonl`

## 2.5 Windows 可分发打包（免 Python）

目标产物：`NewAIHuman_Win64.zip`，用户解压后双击 `NewAIHuman.exe` 即可运行。

### 本地打包命令（Windows）

```bat
build_win.bat
```

脚本会自动完成：
1. 创建 `.venv`（若不存在）
2. 安装 `requirements.txt`
3. 安装 `pyinstaller`
4. 打包桌面入口 `app.desktop.main_desktop`
5. 产出 `dist/NewAIHuman/NewAIHuman.exe`
6. 生成 `NewAIHuman_Win64.zip`（包含 exe、output 目录和 `README_使用说明.txt`）

### 资源与路径说明

- 打包时通过 PyInstaller `--add-data "scripts;scripts"` 打入脚本资源：
  - `scripts/idle_lines_zh.txt`
  - `scripts/reply_templates_zh.txt`
- 程序内已实现资源路径兼容（支持 `sys._MEIPASS`）。
- 运行时输出写到可执行文件同级目录下：
  - `output/audio`
  - `output/events`

### CI 自动打包（可选）

已提供 GitHub Actions：`.github/workflows/build-windows.yml`
- 触发方式：
  - 手动 `workflow_dispatch`
  - push tag `v*`
- 产物：上传 `NewAIHuman_Win64.zip` artifact

## 3. 如何测试（网页 + curl）

### 3.1 网页方式
1. 打开 `http://127.0.0.1:8000/ui`
2. 输入 `user_id` 和评论文本
3. 点击“发送”
4. 页面会显示：最近评论与系统决策、最近一次 `last_event.json`

### 3.2 curl 方式（PowerShell 可改成 `curl.exe`）

```bash
curl -X POST http://127.0.0.1:8000/api/mock/push \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","text":"你好","ts":1730000000}'
```

返回包含：是否 accepted、分类 category、去重/限频命中状态、动作 action。

### 3.3 UI 状态接口

- `GET /api/ui/state`
- 返回：`last_event`（不存在时为空对象）+ `recent`（最近评论/处理结果）

## 4. 两种评论源与切换

配置在 `.env`：

- `SOURCE_TYPE=mock`（默认）
- `PLATFORM_API_ENABLED=false`（默认）

### 4.1 MockSource（可直接跑）
- API：`POST /api/mock/push`
- UI：`GET /ui` 输入框提交即走 mock push

### 4.2 PlatformApiSource（接真实平台骨架）
实现文件：`app/sources/platform_api.py`

已预留：
- `fetch_comments()`：轮询拉取评论
- `connect()`：websocket/long-poll 接入
- `parse_response()`：平台返回统一成 `Comment(user_id/text/ts/raw)`

启用方式（示例）：
1. `.env` 改 `PLATFORM_API_ENABLED=true`
2. 配置：`PLATFORM_BASE_URL`、`PLATFORM_TOKEN/PLATFORM_API_KEY`、`PLATFORM_ROOM_ID/PLATFORM_STREAM_ID`
3. 按平台实现 TODO 方法

**注意**：
- `enabled=false` 时不会影响主服务。
- `enabled=true` 但缺配置时，只打清晰错误日志，不会导致 FastAPI 崩溃。

## 5. 流水线与状态机行为

- 去重：`text + user_id` 哈希，TTL 默认 60s
- 限频：
  - 同用户 10s 内最多 1 条
  - 全局 1s 内最多 3 条
- 分类：`greeting / price / feature / other`
- 状态机：
  - Idle：无评论时每隔 `IDLE_INTERVAL_SECONDS` 输出讲解台词
  - Engage：收到评论后按分类生成回复文本
  - Speak：调用 TTS 生成 wav + 写事件 JSON
  - Cooldown：短暂冷却，避免刷屏

## 6. 输出文件在哪里看

- 语音文件：`output/audio/*.wav`
- 最近事件：`output/events/last_event.json`（覆盖）
- 历史事件：`output/events/history_YYYYMMDD.jsonl`（追加）

事件结构至少包含：
- `event_id, ts, type, text, audio_path, source, meta`

## 7. 替换成真实 TTS 的位置

- 接口：`app/tts/base.py` (`synthesize(text, out_path) -> out_path`)
- 默认实现：`app/tts/silent_wav.py`（纯标准库生成可播放静音 wav）

你可新建例如 `edge_tts_provider.py` 并在 `app/main.py` 注入替换。

## 8. 运行测试

```bash
pytest -q
```

## 9. 常见问题

1. **/ui 404 或打不开**
   - 先确认你是从仓库根目录启动：`uvicorn app.main:app --reload`
   - 检查访问地址是否为 `http://127.0.0.1:8000/ui`
2. **端口占用**
   - 修改 `.env` 中 `PORT` 或启动时指定 `--port`。
3. **看不到 wav 文件**
   - 先确认请求被 accepted；若被去重/限频拦截不会生成新 wav。
4. **平台 API 开了但不工作**
   - 检查 `.env` 平台配置是否完整。
   - 查看日志中 `PlatformApiSource enabled but missing config...` 报错。
