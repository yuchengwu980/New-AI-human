# PLAN（最小改动路线图：A/B/C/D）

> 原则：**只做增量，不改架构，不换入口，不破坏输出协议/目录/打包链路**。

## 阶段 A：基线冻结与可观测性补齐（低风险）

### 目标
- 先把“当前行为”固化为可验证基线，避免后续升级误伤已有能力。

### 改动文件（现有）
- `tests/test_ui.py`：补充 `/api/ui/state` 基线断言（字段存在、结构稳定）。
- `tests/test_desktop_api.py`：补充 result 字段完整性断言（`category/dedup_hit/ratelimit_hit/reply_text/audio_path/event_json`）。
- `README.md`：增加“基线行为不变承诺”小节（对外说明）。

### 新增文件
- `tests/test_output_contract.py`（新增）：验证 `last_event.json` 与 `history_*.jsonl` 字段契约。

### 验证
1. `pytest -q tests/test_dedup.py tests/test_ratelimit.py tests/test_state_machine.py tests/test_output_contract.py`
2. `python -m py_compile $(rg --files app tests -g '*.py' | tr '\n' ' ')`

---

## 阶段 B：现有 pipeline 插件点增强（不改协议）

### 目标
- 在 `orchestrator` 的现有流程中插入“可选 integration 步骤”，默认关闭，保证旧行为不变。

### 改动文件（现有）
- `app/pipeline/orchestrator.py`：插入 pre/post hook 调用点（默认 no-op）。
- `app/config.py`：新增 hook 开关配置（默认 false）。
- `app/models.py`：必要时仅扩展 `meta` 子字段（保持原字段不删不改名）。

### 新增文件
- `app/integrations/__init__.py`
- `app/integrations/base.py`（定义 hook 接口）
- `app/integrations/noop.py`（默认实现）

### 验证
1. 关闭 hook（默认）时，`/api/mock/push` 与 desktop 行为与基线一致。
2. 打开 hook（测试环境）时，`event.meta` 有可预测扩展字段但不破坏旧字段。
3. 运行：`pytest -q`（至少核心用例+契约用例）

---

## 阶段 C：桌面 UI 小增强（仅加按钮/配置，不改主流程）

### 目标
- 在现有 `app.desktop.main_desktop` 上增加可用性配置，不拆 UI 结构。

### 改动文件（现有）
- `app/desktop/main_desktop.py`：
  - 增加“导出当前 event JSON”按钮
  - 增加“复制 audio_path”按钮
  - 增加“打开 history 文件”按钮
- `app/desktop/ui_helpers.py`：补充复制/导出相关 helper。
- `README.md`：补充新按钮说明。

### 新增文件（可选）
- `tests/test_desktop_helpers.py`（仅 helper 层，不依赖 GUI 启动）

### 验证
1. 人工：窗口操作按钮均可用，失败提示清晰。
2. 输出目录与命名规则不变：`output/audio`、`output/events/last_event.json`、`history_YYYYMMDD.jsonl`。
3. `python -m py_compile ...` 通过。

---

## 阶段 D：打包与发布增强（保留现有 PyInstaller/Workflow）

### 目标
- 仅修复/增强现有 `build_win.bat` 与 workflow，不替换打包方式。

### 改动文件（现有）
- `build_win.bat`：
  - 增加构建前清理与构建后校验（检查 exe、zip、关键目录）
  - 增加失败码与错误提示细化
- `.github/workflows/build-windows.yml`：
  - 增加 artifact 命名含版本/commit（可选）
  - 增加打包后文件存在性检查步骤
- `docs/README_使用说明.txt`：补充发布包校验说明（文件列表、首次运行建议）。
- `README.md`：补充“发布者检查清单”。

### 新增文件（可选）
- `scripts/check_package.ps1`（校验 zip 内容与关键文件）

### 验证
1. 本地执行 `build_win.bat` 成功产出：
   - `dist/NewAIHuman/NewAIHuman.exe`
   - `NewAIHuman_Win64.zip`
2. zip 内检查（手工或脚本）：README、output 目录、exe 均存在。
3. CI workflow 触发后可下载 artifact。

---

## 每阶段通用“不破坏”检查

1. 入口不变：
   - `python -m app.main`
   - `python -m app.desktop.main_desktop`
2. 输出协议不变：
   - `last_event.json` 字段：`event_id/ts/type/text/audio_path/source/meta`
   - `history_YYYYMMDD.jsonl` 按行追加 JSON
3. 打包方式不变：
   - 保持 PyInstaller + 现有 workflow 主路径
4. 回归命令：

```bash
pytest -q tests/test_dedup.py tests/test_ratelimit.py tests/test_state_machine.py
python -m py_compile $(rg --files app tests -g '*.py' | tr '\n' ' ')
```
