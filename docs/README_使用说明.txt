【NewAIHuman 桌面版使用说明】

1) 运行方式
- 下载并解压 NewAIHuman_Win64.zip。
- 双击 NewAIHuman.exe 启动程序（无需安装 Python）。

2) 基本操作
- 在窗口中输入 user_id（默认 u1）和评论文本。
- 点击“发送”或在评论框按回车。
- 可用快捷按钮：问价格 / 问功能 / 你好。
- 打开 Idle 开关后会按间隔自动生成 idle_line。

3) OBS 联动配置（字幕 + 音频）
在 OBS 中先创建并命名以下 Source：
- 字幕源（Text/GDI+）：建议名称 `字幕`
- 媒体源（Media Source）：建议名称 `TTS音频`

然后在桌面客户端的“OBS 输出器（阶段A）”区域填写：
- Host：127.0.0.1
- Port：4455（按 OBS WebSocket 设置）
- Password：OBS WebSocket 密码
- 字幕源名称：与 OBS 中 Text Source 名称一致（默认 `字幕`）
- 音频源名称：与 OBS 中 Media Source 名称一致（默认 `TTS音频`）
- 勾选“启用OBS自动推送”并点击“连接 OBS”
- 点击“测试推送”验证连通

4) 输出文件位置
- 音频文件：output/audio/*.wav
- 最新事件：output/events/last_event.json
- 历史事件：output/events/history_YYYYMMDD.jsonl

5) 3分钟复现（可直接照做）
- 第1步：打开 OBS，确认已启用 obs-websocket（默认 4455），并创建 `字幕` 与 `TTS音频` 两个源。
- 第2步：启动 NewAIHuman，OBS 区域填好连接信息，点击“连接 OBS”。
- 第3步：输入“你好”点击发送。
  - 你会看到 OBS 的字幕源文本变化为最新回复。
  - 你会听到 OBS 的媒体源播放最新 wav。
  - 本地同时写出 `output/events/last_event.json` 与 `output/audio/*.wav`。

6) 常见问题
- 无法写入文件：请不要在受限目录直接运行（例如系统目录），建议放在桌面或D盘普通目录。
- 杀毒软件误报：部分打包程序会触发误报，可加入白名单后重试。
- 启动失败提示缺少运行库：请安装 Microsoft Visual C++ Redistributable（x64）后重试。
- OBS 连接失败：检查 OBS 是否启用 WebSocket、端口和密码是否一致、防火墙是否拦截。
- 双击无响应：右键“以管理员身份运行”或在命令行执行 NewAIHuman.exe 查看提示。


7) 阶段B输入适配层（可选）
- 输入方式可选：manual_ui / http_post_/comment / file_tail。
- HTTP 转发示例：
  curl -X POST http://127.0.0.1:8000/comment -H "Content-Type: application/json" -d '{"user_id":"u1","text":"你好","msg_id":"m-001"}'
- 文件监听示例（默认 output/input_comments.txt）：
  {"user_id":"u2","text":"问下价格","msg_id":"m-002"}
  或
  u3|这个有哪些功能？|1730000002|m-003


8) 阶段C Provider（联网可选）
- 默认离线：LLM=mock，TTS=silent。
- 若要在线能力：在桌面端 Provider 区域选择 `openai`，填入 Key/Model/Timeout 后点击“应用 Provider 配置”。
- 失败自动回退：
  - LLM 失败 -> 使用 mock 模板回复
  - TTS 失败 -> 使用静音 wav
- UI 可看到 Provider 状态（耗时/错误原因/fallback）。

9) 发布包自检（发布者可选）
- 在发布机器命令行执行：
  NewAIHuman.exe --help
  NewAIHuman.exe --selfcheck
- 若 selfcheck 返回成功，说明核心模块可加载、运行目录可写。
