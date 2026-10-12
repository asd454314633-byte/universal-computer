# PROVIDERS.md — 全部 Provider 动作清单与 CLI 用法

所有命令入口：`python <UC_HOME>/uc.py <子命令>`，stdout 恒为单个 JSON。
全局参数：`--headed`（前台浏览器）、`--profile <dir>`（持久登录态）、
`--cdp <endpoint>`（attach 已运行浏览器）、`--webmcp`（实验性探测，默认关）、
`--visual`（允许视觉兜底，默认关）。

## 1. Browser（Playwright 主 Provider）

```bash
uc.py browser open --url https://example.com
uc.py browser read --selector "#title"          # 读文本
uc.py browser fill --selector "#q" --value "hello"
uc.py browser click --selector "#go"
uc.py browser screenshot --path out.png
uc.py inspect site --url https://example.com    # 只读侦察（快照+要点）
```

动作名（task.json / API）：`open / read_text / snapshot / screenshot /
list_tabs / switch_tab / fill / upload / download / click`。

覆盖能力：语义定位（selector，不依赖屏幕坐标）、多标签页、iframe、
dialog、上传下载、截图、DOM/无障碍快照、登录态 Profile、attach 已有浏览器。

## 2. Windows UIA / Win32

```bash
uc.py windows list
uc.py windows read_tree --window-name "窗口标题" --depth 4
uc.py windows set_text --window-name "窗口标题" --criteria '{"control_type":"edit"}' --value "文本"
uc.py windows invoke --window-name "窗口标题" --criteria '{"control_type":"button","name":"确定"}'
uc.py inspect window --name "窗口标题"
```

动作名：`list_windows / read_tree / get_value / find_control / focus /
set_text / invoke / type_text`。

定位优先用结构属性：`AutomationId / Name / ControlType / ClassName` +
层级关系（criteria JSON）。支持 Button/Edit/List/Tree/Menu/ComboBox/
Checkbox/Tab/Dialog/Toolbar；动作链 Pattern → WM 消息 → 键盘。
**禁止用固定绝对坐标完成整个任务。**

## 3. COM / 原生接口

Phase 1 提供 COM Provider 接口与注册表探测（Excel/Word/Office/Shell 预留）。
task step 带 `"use_com": true` 时路由优先尝试 COM。
有成熟 COM 接口的应用（如 Office），必须走 COM，禁止视觉点击几十次。

## 4. CLI / PowerShell / Python

本 Skill 不限制"只能 GUI"。凡是 CLI/脚本更可靠的任务（文件批处理、
进程查询、系统信息、SHA256、Git 等），直接在宿主 shell 执行，
不必经过 Core。Core 的价值在 GUI 与浏览器结构化路径。

## 5. File 操作

Core 未内置专门 file provider——文件操作走宿主 shell（Read/Write/PowerShell）。
高风险删除/覆盖沿用用户全局风险原则（见 RISK.md）。

## 6. Visual Provider（兜底接口）

统一 `VisualProvider` 接口：`observe / locate / click / type / scroll /
drag / verify`。不锁定具体模型（可接 OpenAI Computer Use / Fara /
UI-TARS / Gemini Computer Use / 宿主自带 CUA）。
默认关闭；显式 `--visual` 开启后才参与 fallback 阶梯最后一级。

## 返回 JSON 契约

成功：
```json
{"success": true, "provider": "playwright", "action": "click",
 "result": {"clicked": "#go"}, "duration_ms": 42, "error": null, "recovered": false}
```
失败（结构化 error）：
```json
{"success": false, "error": {"type": "LOCATE_FAILED", "phase": "locate",
 "retryable": true, "degrade_allowed": true, "raw": "..."}}
```
错误类型：`PROVIDER_UNAVAILABLE / LOCATE_FAILED / TIMEOUT /
PERMISSION_DENIED / RUNTIME_ERROR / UNSUPPORTED_ACTION`。

## 声明式任务（uc.py run task.json）

```json
{
  "task_id": "example-task",
  "domain": "browser" | "windows" | "auto",
  "steps": [
    {"step_id": "s1", "action": "open", "params": {"url": "..."},
     "risk": "READ",            // 可选：只能升级不能降级
     "provider": "playwright",  // 可选：钉死 Provider
     "use_com": false}          // 可选：windows 域尝试 COM
  ]
}
```
带状态机、失败恢复（重获取→重定位，硬上限 2 次）、逐动作 JSONL 审计。
