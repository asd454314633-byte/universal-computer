# 10_SKILL_INVENTORY.md — 电脑操作能力全盘盘点（V1.1 Routing Consolidation）

日期：2026-10-04 ｜ 范围：WorkBuddy / Codex / Qoder CN 三宿主 + 用户级规则
方法：目录扫描（`~/.workbuddy/skills`、`~/.codex/skills`、`~/.qoder-cn/skills`=junction）、
WorkBuddy 内置插件 Skill、用户级 MEMORY.md 规则。与电脑操作无关的 Skill（ComfyUI、
QR/微信、设计、金融、文档等）不在路由冲突面内，仅登记不分类。

## 一、直接参与路由的 Skill（冲突面）

| Skill | 宿主 | 职责 | 与 universal-computer 关系 | 分类 |
|---|---|---|---|---|
| universal-computer | WB+Qoder(junction)+Codex | 唯一整机操作 Router（Browser/UIA/Win32/COM/CLI/Visual 接口） | 本体 | **KEEP（canonical Router）** |
| cua-gui-first-router | WB | 声称"凡 GUI 动作默认 CUA-first，禁止 PowerShell/cmd/Python" | **直接冲突**：抢路由权 + 与新架构（CLI 优先、CUA 兜底）相反 | **DEPRECATE→改写**（降级为 Visual Provider 使用规程，仅在 UC Router 指定 visual 时参考；其 GUI_SUCCESS_PLAYBOOK 知识保留） |
| cua-element-token-chromium-drive | WB | Cua MCP 拿不到 element_token 时走厂商 CLI 驱动 Chromium | Visual Provider 的实现技巧，被 UC visual 路径按需引用 | **DELEGATE**（仅 UC Router 调用） |
| cua-uia-health-smoke-recovery | WB | Cua daemon 健康/卡死恢复 | Cua 作为 Provider 的运维规程 | **KEEP**（Provider 附属，非路由竞争者） |
| windows-interactive-launch | WB | GUI 程序交互式启动全局规则 | 互补：UC 启动 GUI 程序时遵守 | **KEEP** |
| agent-browser | WB 内置插件 | 浏览器自动化（打开/点击/截图/提取） | 浏览器 Provider 竞争者 | **DELEGATE**（UC Router 内部可选实现；不自动触发普通浏览器任务） |
| playwright-cli | WB 内置插件 | Playwright CLI 浏览器自动化 | 与 UC 核心同根（Playwright） | **DELEGATE**（UC 已内置 Playwright Provider；插件仅在显式要求 CLI 形态时用） |
| universal-computer（Codex 副本） | Codex | 同 canonical | 由 sync_skill.py 生成 | **KEEP**（副本，禁手改） |

## 二、领域专用 Skill（非路由竞争者，KEEP）

排查后确认以下 Skill 是**特定故障/场景的方法论**，不与 Router 抢普通电脑任务，
由 UC Router 在命中对应场景时**委托**使用：

- windows-app-silent-exit-orphan-child（应用秒退/孤儿进程）
- windows-app-total-uninstall-forensics（彻底卸载）
- windows-atomic-state-write-hardening（状态写失败）
- windows-logon-daemon-persistence / windows-process-supervisor-vbs（常驻/守护）
- windows-winrt-ocr-ps51（WinRT OCR）
- wsl-host-mediated-execution（WSL 驱动）
- electron-asar-chinese-error-forensics（Electron 报错取证）
- tk-controller-ui-lock-heal（Tk 控制器修复）

## 三、规则层（Prompt/Instructions/Memory）

| 规则 | 位置 | 冲突 | 处置 |
|---|---|---|---|
| 《GUI 执行总则：所有 Windows GUI 操作默认 CUA-first》 | 用户级 `~/.workbuddy/MEMORY.md` | **与 V1.1 架构相反**（CUA 应为 fallback） | **改写**：路由权移交 universal-computer Router；CUA 降为 visual fallback；PLAYBOOK 复用纪律保留并入 Router |
| 《Agent 最大能力执行原则》 | 用户级 MEMORY.md | 无冲突（风险分级与 UC RISK.md 一致） | KEEP |
| AGENTS.md（项目级） | 各项目 | 未发现电脑操作路由规则 | KEEP |

## 四、Codex / Qoder 冲突面

- Codex：`~/.codex/skills` 内 hyperframes*（创作）、agent-flow-codex、media-use
  均非电脑操作路由竞争者。**Codex 冲突 = 0**。
- Qoder CN：skills 为 WorkBuddy junction，冲突面与 WorkBuddy 相同；
  Qoder 内置 computer-use 能力（`~/.qoder-cn/bin/qoder-cn-computer-use`）
  属宿主自带工具，按任务书 §17 原则由 Adapter 调用、不绑 Core。

## 五、重复自动触发 / 递归 / 循环风险清单

1. **cua-gui-first-router vs universal-computer**：同为"路由器"定位，GUI 任务
   可能双触发 → 本轮收敛为单一 Router。
2. **用户记忆 CUA-first 规则 vs UC Router**：模型行为层冲突 → 改写记忆。
3. **agent-browser/playwright-cli vs UC browser Provider**：普通浏览器任务
   可能双触发 → 描述不改（官方插件），由 ROUTING_POLICY 声明优先级。
4. **递归调用**：UC Router → cua-pilot MCP →（无再触发 Skill 路径）→ 无递归。
   UC SKILL.md 明令"禁止绕过路由逐个盲试 Provider"，fallback 上限见 ROUTING_POLICY。
5. **fallback 循环**：UC Core 恢复硬上限 2 次 + Router 候选上限 2（至多 3），
   不存在无限循环路径。
