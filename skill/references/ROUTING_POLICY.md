# ROUTING_POLICY.md — 唯一整机操作路由策略（canonical，三宿主共用）

版本：`ucrout-v1.1-20261004`（冻结版追加 §7 不变量）
规范唯一源：`UniversalComputer/skill/references/ROUTING_POLICY.md`
宿主副本由 `adapters/sync_skill.py` 同步，**禁止宿主各自维护/修改路由规则**。

> **真源声明**：本文件是路由策略的唯一规范源；`provider_registry.json`
> 是它的机器可读投影，不是第二套独立策略源。两者与三宿主副本语义必须一致；
> 冲突时以本文件为准并判 `ROUTING_POLICY_SYNC = FAIL`（见 §7.1）。

## 0. 单一 Router 原则

- `universal-computer` 是**唯一**自动触发的整机操作 Skill。
- 普通电脑任务（打开/点击/输入/浏览/下载/文件/系统/软件操作）**只由
  universal-computer 自动触发**；其他任何电脑操作类 Skill（CUA/Browser/
  Playwright/UIA 类）不得抢先自动触发，只能被 Router 内部选择或被用户显式点名。
- 宿主内置工具（cua-pilot MCP、agent-browser 插件、Qoder computer-use 等）
  是 Provider 实现细节，对用户不可见，不参与 Skill 层竞争。

## 1. Domain-Aware Routing

**不存在全局固定 Provider 顺序。** 先分类任务域，再在域内按可靠性/成本排序：

```
先分类任务域 → 域内排序 → 选 1 个 primary → 最多保留 1 个正常 fallback
→ 特殊情况下最多 3 个候选
```

各任务域内阶梯（域内优先级，非全局顺序）：

| 任务域 | 域内阶梯 |
|---|---|
| 网页 | API/MCP → Playwright → Visual |
| Office | 原生API/COM → UIA → Visual |
| 文件/系统 | CLI/File API → Win32/UIA → Visual |
| 标准桌面 GUI | UIA/Win32 → Visual |
| 自绘/特殊 UI | Visual 可直接成为 Primary |

反例约束（防误路由）：改 Excel 单元格不走 Playwright；关闭 Chrome 走
CLI/Win32 而非 Playwright；标准 Windows 对话框直接 UIA 不先试别的。

- **Visual CUA 定位**：①自绘/无结构面界面可直接 Primary；②其余域仅作
  结构化失败后的 fallback。默认不参与网页与标准控件任务的竞争。
- **Provider 上限**（精确语义见 §7.2）：
  - `INITIAL_TOP_K_PROVIDERS = 2`（普通任务默认 2 个初始候选）
  - `MAX_RETRIES_PER_PROVIDER = 2`（同 Provider 内重获取→重定位→重试）
  - `MAX_PROVIDER_SWITCHES = 2`（Primary→Fallback1 = 第 1 次切换；
    Fallback1→Fallback2 = 第 2 次切换，即一条任务最多实际进入 3 个 Provider）
  重试与切换是不同概念的独立计数器，禁止把"每 Provider 重试"累积成
  无限换 Provider 链（Playwright→UIA→Win32→Visual→… 不允许）。

## 2. Cost Model（同分时按此排序）

cost = 预计耗时 × 失败概率 × 副作用面。静态权重（低→高）：
`api/mcp(1) < cli(2) < playwright(3) < com(3) < uia(4) < win32(4) < visual(9)`
Visual 权重最高 = 默认最后；自绘界面场景将其视为唯一可用域，权重重置为 2。

## 3. Capability Cache（静态能力与运行时健康分开缓存）

| 缓存层 | 内容 | TTL |
|---|---|---|
| installed capability cache | Provider 是否安装、CLI 是否存在、COM 是否注册、Playwright 是否安装 | **24h**（`logs/state/capability_cache.json`） |
| runtime healthy cache | Provider 本会话内最近一次成功 | session 级（会话结束即失效） |
| runtime degraded cache | 一次临时失败（浏览器 session 异常、UIA 某次打不开等） | **5–15 min**，过期自动重试，禁止因偶发故障降级一整天 |
| process/window availability | 目标进程/窗口是否在场 | 实时或极短 TTL（≤60s） |

- 偶发失败只进 `runtime degraded`（短 TTL），**不得**写进 24h 静态缓存。
- Provider 恢复路径：短 TTL 自然过期，或 `doctor` 重新全绿立即复位。

## 4. 冲突审计

- 任何"两个以上电脑操作类 Skill 同时主张同一任务"的事件，记入
  `evidence/audit/` 路由冲突行（`conflict_skills` 字段）。
- 用户显式点名其他 Skill（如"用 playwright-cli"）不记冲突，Router 记
  `explicit_override` 并放行（覆盖边界见 §7.4）。

## 5. 触发词与让位规则

- UC description 覆盖：操作电脑/打开软件/打开网页/点这个窗口/填表/下载/
  上传/自动化电脑任务/操作这个程序。
- 让位例外（UC 不抢）：用户显式点名其他 Skill；任务本质是领域问题
  （QR 识别、LoRA 训练、文档排版等→对应领域 Skill，UC 仅在其内部需要
  GUI/浏览器动作时被其调用，形成合法委托而非竞争）。
- UC → 领域 Skill 的调用是合法的（UC 作为执行层）；领域 Skill → UC 的
  调用同样合法（UC 作为能力层）。禁止的是：两个**路由器**同时决策同一任务；
  跨 Skill 委托受 §7.3 递归守卫约束。

## 6. 三宿主一致性

WorkBuddy / Codex / Qoder CN 的本文件与 provider_registry.json 必须逐字节
一致（sync_skill.py --check 校验）。宿主差异只允许存在于 Adapter
（如何启动进程/如何读 JSON），不允许存在于路由规则。

## 7. Canonical / Recursion / Override Invariants

### 7.1 Canonical Source

`ROUTING_POLICY.md` 是路由策略的唯一规范源。

`provider_registry.json` 是该策略的机器可读投影，不是第二套独立策略源。

要求：

```
ROUTING_POLICY.md → provider_registry.json → 三宿主副本
```

三者语义必须一致。

如 registry 与 ROUTING_POLICY 冲突：`ROUTING_POLICY.md` 优先，
并判定 `ROUTING_POLICY_SYNC = FAIL`，禁止宿主自行选择其中一份继续维护。
`sync_skill.py --check` 必须验证两者语义一致，否则 FAIL。

### 7.2 Provider Limits

```
INITIAL_TOP_K_PROVIDERS  = 2
MAX_RETRIES_PER_PROVIDER = 2
MAX_PROVIDER_SWITCHES    = 2
```

- 普通任务默认只产生 2 个初始候选；只有存在明确特殊原因时，允许准备第 3 个候选。
- Provider switch 以**实际执行 Provider 的变化**计数：

```
Primary   → Fallback1 = switch 1
Fallback1 → Fallback2 = switch 2
```

- 达到上限后禁止继续切换 Provider（一条任务最多实际进入 3 个 Provider）。

### 7.3 Cross-Skill Recursion Guard

允许 `Domain Skill → universal-computer`（执行具体电脑操作）；
允许 `universal-computer → Domain Skill`（移交明确的领域语义任务）。

但**同一 task_id 禁止 Router 递归重新决策**：

```
ROUTER_REENTRY_SAME_TASK = FORBIDDEN
CALL_DEPTH_MAX           = 4
```

- 合法：`Domain Skill → universal-computer → Playwright`
- 禁止：`universal-computer → Domain Skill → universal-computer → Domain Skill → …`

即：UC 已把业务语义交给某领域 Skill 后，该领域 Skill 只能调用 UC 的
**具体执行能力**，不能再次要求 UC 重新决定"这个任务该交给哪个领域 Skill"。

每次跨 Skill 委托必须记录：`task_id / parent_skill / child_skill /
delegation_reason / call_depth`（写入 evidence/audit）。

### 7.4 Explicit Override

用户显式指定（"使用 Playwright"/"不要使用 CUA"/"使用 UIA"）允许覆盖正常
Provider 排序，并记录 `explicit_override = true`。

但 `explicit_override` **只能覆盖路由选择**，不得覆盖：

- 安全规则
- 风险等级
- SSRF Guard
- 权限边界
- 高风险不可逆动作确认
- 审计要求
- Provider 自身硬性安全限制
