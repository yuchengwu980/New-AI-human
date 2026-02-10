【NewAIHuman 桌面版使用说明】

1) 运行方式
- 下载并解压 NewAIHuman_Win64.zip。
- 双击 NewAIHuman.exe 启动程序（无需安装 Python）。

2) 基本操作
- 在窗口中输入 user_id（默认 u1）和评论文本。
- 点击“发送”或在评论框按回车。
- 可用快捷按钮：问价格 / 问功能 / 你好。
- 打开 Idle 开关后会按间隔自动生成 idle_line。

3) 输出文件位置
- 音频文件：output/audio/*.wav
- 最新事件：output/events/last_event.json
- 历史事件：output/events/history_YYYYMMDD.jsonl

4) 常见问题
- 无法写入文件：请不要在受限目录直接运行（例如系统目录），建议放在桌面或D盘普通目录。
- 杀毒软件误报：部分打包程序会触发误报，可加入白名单后重试。
- 启动失败提示缺少运行库：请安装 Microsoft Visual C++ Redistributable（x64）后重试。
- 双击无响应：右键“以管理员身份运行”或在命令行执行 NewAIHuman.exe 查看提示。
