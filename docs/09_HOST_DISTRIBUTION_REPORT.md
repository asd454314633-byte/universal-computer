# 09_HOST_DISTRIBUTION_REPORT.md — UNIVERSAL_COMPUTER_SKILL_V1 验收报告

日期：2026-10-04 ｜ 环境：Windows 11 ｜ Core 运行 venv：`~/.workbuddy/binaries/python/envs/default`
（依赖与 `requirements.lock.txt` 一致：playwright 1.55.0 / uiautomation 2.0.29 / comtypes 1.4.17 / pywin32 312，doctor 全绿 + 浏览器实启成功）

## 一、本阶段产出

| 产物 | 位置 | 说明 |
|---|---|---|
| SKILL.md 重写 | `skill/SKILL.md` | 双语 description 覆盖真实用户说法（自动触发用）；正文精简，Progressive Disclosure 指向 references |
| references/ 4 篇 | `skill/references/` | PROVIDERS（全动作清单+CLI）、ROUTING_RECOVERY、RISK（§10 用户权限原则全文）、INSTALL（三宿主分发） |
| scripts/uc.cmd | `skill/scripts/` | 宿主中立 CLI 包装：解析 UC_HOME → 调 Core → 恒 JSON 输出 |
| examples/ | `skill/examples/` | task_example.json 声明式任务示例 |
| 同步器 | `adapters/sync_skill.py` | canonical→三宿主生成（支持 --check 一致性校验、junction 探测）；宿主副本禁止手改 |

## 二、分发事实

| 宿主 | 安装位置 | 状态 |
|---|---|---|
| WorkBuddy | `~/.workbuddy/skills/universal-computer/` | SYNCED（目录扫描发现机制，与其余 47 个在用 Skill 同机制，无额外注册步骤） |
| Qoder CN | `~/.qoder-cn/skills/universal-computer/` | SYNCED（实测该目录是指向 `~/.workbuddy/skills` 的 junction，一次同步两宿主生效；skill-usage.json 证实为其在用 Skill 源） |
| Codex | `~/.codex/skills/universal-computer/` | SYNCED（codex-cli 0.142.5） |

`sync_skill.py --check` 三宿主全部 MATCH。宿主副本 wrapper（`scripts/uc.cmd`）
实测均能调通 Core（capabilities/doctor JSON 正常返回）。

## 三、验收结果（任务书第二十一节格式）

```text
UNIVERSAL_COMPUTER_CORE        = PASS        # 2026-10-04 14:53 重跑 tests/run_acceptance.py 12/12
UNIVERSAL_COMPUTER_SKILL       = PASS        # SKILL.md + 4 references + scripts + examples

BROWSER_PLAYWRIGHT             = PASS        # B1-B4（打开/读取/填写/点击/扰动恢复）
WINDOWS_UIA                    = PASS        # W1-W4（fixture 窗口/控件树/读写/零坐标）
WIN32                          = PARTIAL     # 枚举/聚焦/消息路径实测可用；完整窗口管理层不在 V1 范围
CLI_POWERSHELL                 = PASS        # uc.py run 真实任务冒烟 + 三宿主 wrapper 实测
FILE_OPERATIONS                = PASS        # 按设计经宿主 CLI/Shell 承载（Skill 已写明指引，不重复造轮子）
VISUAL_PROVIDER_INTERFACE      = PASS        # observe/locate/click/type/drag/scroll/verify（Codex 实测输出确认）
PROVIDER_ROUTER                = PASS        # R1 浏览器→playwright / R2 控件→uia
PROVIDER_FALLBACK              = PASS        # R3 三段式阶梯降级 + F1 恢复（硬上限 2 次）
AUDIT                          = PASS        # evidence/audit/2026-10-03.jsonl + 2026-10-04.jsonl 逐动作 JSONL

WORKBUDDY_SKILL_INSTALLED      = PASS
CODEX_SKILL_INSTALLED          = PASS
QODER_SKILL_INSTALLED          = PASS

WORKBUDDY_AUTO_TRIGGER         = PENDING     # 需用户新开 WorkBuddy 会话说自然语言实测（本会话即宿主，无法自证）
CODEX_AUTO_TRIGGER             = PASS        # codex exec 自动发现：SKILL_FOUND: universal-computer
QODER_AUTO_TRIGGER             = PENDING     # 需用户新开 Qoder 会话实测 /universal-computer 与自动匹配

CANONICAL_SOURCE_COUNT         = 1           # UniversalComputer/skill/
HOST_SPECIFIC_CORE_FORKS       = 0           # 三副本均由 sync_skill.py 生成，--check 可校验

OPENCLAW_DEPENDENCY            = NO
SAM_WECHAT_DEPENDENCY          = NO
QR_DEPENDENCY                  = NO

READY_FOR_DAILY_USE            = YES(条件性) # Codex 全链实测通过；WorkBuddy/Qoder 安装与发现机制
                                              # 已验证，仅剩新会话实机确认（任务 #38），无代码遗留项
```

## 四、关键实测记录

1. **Codex 自动触发（UC-5）**：`codex exec -m gpt-5.5`（config 默认模型
   `gpt-6.1-sol` 对 ChatGPT 账户不可用，models_cache.json 实测仅
   gpt-5.5/codex-auto-review 可用）→ 回答 `SKILL_FOUND: universal-computer`。
2. **Codex 显式调用（UC-6）**：要求用 skill 跑 `scripts/uc.cmd capabilities`
   → 正确解析 JSON 并报告 `uia: true`、visual actions 六项——证明
   Skill→wrapper→Core→JSON 全链在第三方宿主可用。
3. **UC-1..4 本地回归**：12/12 PASS（证据 evidence/B*/W*/R*/F1*.json，
   时间戳 2026-10-04 14:53）+ CLI 冒烟任务 SUCCESS + 审计 JSONL 落盘。
4. **junction 事实**：`~/.qoder-cn/skills` → `~/.workbuddy/skills`（junction），
   任务书第十六节的 `~/.qoder/skills/` 在本机实际为 `~/.qoder-cn/skills/`。

## 五、用户调用方式（第二十二节）

- 自动触发（三宿主一致）：直接说「帮我打开 XX 软件把 XX 做完」「帮我操作电脑完成……」
- 强制调用（三宿主一致）：「使用 universal-computer Skill 完成以下任务：……」
- Qoder 额外支持：`/universal-computer`

## 六、遗留与边界

- WorkBuddy/Qoder 新会话实机触发确认 → 待办 #38（非代码问题）
- COM 仍为接口+探测层（未绑 Office 深度操作）；WIN32 完整窗口管理层待增量升级
- VisualProvider 仅接口+Mock，未接任何真实 CUA 模型（按 V1 设计）
- QR/微信项目保持冻结，未做任何改动
