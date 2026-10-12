---
name: universal-computer
description: >
  Operate the user's Windows computer: desktop applications, browser, files,
  command line, and graphical interfaces. Use this skill when the user asks to
  open, control, click, type, browse, download, upload, configure, inspect,
  automate, or complete any task on the computer. Covers web automation
  (Playwright), Windows UI Automation (UIA), Win32 window/process control,
  COM interfaces, PowerShell/CLI, and file operations, with automatic
  provider routing and fallback. 触发词：帮我操作电脑、打开软件/网页、点这个窗口、
  操作这个程序、填表、下载/上传文件、修改窗口内容、自动化电脑任务、
  完成这个电脑上的操作。Prefer deterministic providers (API/CLI/Playwright/UIA/
  Win32/COM); use visual computer control only as a last-resort fallback.
---

# Universal Computer Skill（通用电脑操作）

宿主中立的整机操作能力。任何能「启动进程 + 解析 JSON」的 Agent 都能调用。

## 什么时候用

用户想让 Agent 在电脑上**实际做事**：操作浏览器、桌面软件、窗口控件、
文件、命令行。凡是"打开/点击/输入/读取/下载/上传/配置/检查"类请求，
先考虑本 Skill，由它自动选择最可靠的执行方式。

## 前置：定位 Core

Core 是一份独立 Python 代码库（不在本 Skill 内）。按顺序解析：

1. 环境变量 `UNIVERSAL_COMPUTER_HOME`
2. 本 Skill 目录下 `scripts/core_path.txt`（分发时写入）
3. 默认安装路径（见 `references/INSTALL.md`）

找到后，所有操作通过 CLI 执行：

```bash
python <UC_HOME>/uc.py doctor          # 首次/异常时先做健康检查
python <UC_HOME>/uc.py capabilities    # 各 Provider 可用性
python <UC_HOME>/uc.py run task.json   # 声明式多步任务
python <UC_HOME>/uc.py browser ...     # 浏览器单动作
python <UC_HOME>/uc.py windows ...     # Windows 窗口/控件单动作
python <UC_HOME>/uc.py inspect ...     # 只读侦察
```

stdout 恒为单个 JSON 文档（`success/provider/action/result/duration_ms/error`）。
完整命令与参数见 `references/PROVIDERS.md`。

## 执行路由（权威规则：references/ROUTING_POLICY.md + provider_registry.json）

**本 Skill 是唯一自动触发的整机操作 Router**。其他电脑操作类 Skill
（CUA/Browser/Playwright/UIA 类）不得抢普通电脑任务，只能被本 Router
内部选择或被用户显式点名。

```
任务 → 现成 API / MCP / CLI？ → 是：直接用
     → 浏览器任务？ → Playwright（内置）→（特殊场景+1 候选）→ Visual CUA
     → 文件/系统任务？ → CLI（PowerShell 优先）
     → Office？ → COM/原生接口
     → 标准 Windows 控件？ → UIA → Win32
     → 自绘界面/结构化全败？ → Visual CUA（唯一兜底）
```

- **Domain-aware routing：不存在全局固定 Provider 顺序**——先分类任务域，
  再在域内按可靠性/成本选 primary + 至多 1 个正常 fallback（特殊至多 3 候选）。
- 两个独立上限：`MAX_RETRIES_PER_PROVIDER = 2`（同 Provider 内重试）；
  `MAX_PROVIDER_SWITCHES = 2`（整条任务最多换 2 次 Provider，禁止链式膨胀）。
- **Visual CUA 默认不参与网页/标准控件竞争**：仅自绘界面（可直接 Primary）
  或结构化路径失败后启用。
- cost model / 分层 capability cache（静态 24h / 运行时短 TTL）/ 冲突审计
  见 ROUTING_POLICY.md。

## 长驻服务的可见控制台

- 当用户或项目规则要求服务运行时可见，启动本机数字人、Avatar、WebRTC 或其他长驻服务时，必须创建独立的用户可见控制台；不得把服务放进 Codex PTY、headless conhost、隐藏窗口或仅写日志的后台进程。
- 控制台标题应标明服务端口/URL，并实时显示 stdout/stderr、进度与错误。Python 使用 `-u` 或 `PYTHONUNBUFFERED=1`；日志文件只能作补充。
- 启动后分别验证端口就绪和窗口可见。不能用 HTTP/API 可访问来代替窗口可见性证据；窗口不可见时不得称启动符合要求。
- 仅当用户针对当前这一次启动明确要求无头运行时，才允许无头例外。其他历史任务中的启动方式不构成授权。
- 重启前检查活动连接/任务。若优雅关闭失败，先查明并报告监听进程状态，使用精确且已核实的收尾方式后再重启；不得遗留无头服务并宣称任务完成。

## 风险策略（继承用户全局原则，不要每步询问）

- **READ / WRITE（浏览、点击、输入、填表、打开网页/软件、普通文件操作）：
  默认直接执行**，不要停下来确认。
- **DESTRUCTIVE（删除不可恢复数据、覆盖唯一原件、支付/转账、对外发布、
  系统级配置、凭据/提权、其他明显不可逆操作）：最终不可逆一步前确认。**
- Core 对每个动作声明风险等级（`RISK_MAP`），DESTRUCTIVE 动作默认返回
  `PERMISSION_DENIED`，由调用宿主确认后重发（task step 可带 `risk` 覆盖升级）。

## 失败处理（简要；详见 references/ROUTING_RECOVERY.md）

```
识别失败 → 重新观察(inspect) → 重定位 → 重试(硬上限2次) → 必要时切 Provider
```

- Playwright selector 失效 → 重新 snapshot 后修 selector
- DOM 不可访问 → 切 UIA/Win32/Visual
- UIA 控件不可见 → Win32 消息/键盘 → Visual
- CLI 更简单 → 直接切 CLI
- 禁止无限循环重试；错误 JSON 恒带结构化 `error`（type/phase/retryable）。

## 证据

每个动作自动写入 JSONL 审计日志（`evidence/audit/`）：
`task_id/provider/action/target/result/duration/fallback_reason/error`。
复杂任务按需补截图/快照，不要制造大量无价值截图。

## 深入阅读（按需加载）

- `references/PROVIDERS.md` — 全部 Provider 的动作清单与 CLI 参数
- `references/ROUTING_RECOVERY.md` — 路由架构、fallback 阶梯、恢复策略
- `references/RISK.md` — 风险分级与用户权限原则全文
- `references/INSTALL.md` — 安装、venv、doctor、宿主分发与同步
- `examples/task_example.json` — 声明式任务格式示例
