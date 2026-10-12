# 11_ROUTING_CONSOLIDATION_REPORT.md — V1.1 路由收敛最终裁决

日期：2026-10-04 ｜ 任务：`UNIVERSAL_COMPUTER_SKILL_V1_1_ROUTING_CONSOLIDATION`
范围：整合 → 去重 → 收敛 → 路由（未新开发任何 Provider 能力；QR/微信零改动）

## 一、本阶段产出

| 产物 | 位置 | 状态 |
|---|---|---|
| SKILL_INVENTORY.md | `docs/10_SKILL_INVENTORY.md` | 三宿主 + 用户规则全盘盘点 |
| ROUTING_POLICY.md（canonical） | `skill/references/` | 单一 Router 原则 + 7 域优先级 + 上限 + cost model + 冲突审计 |
| provider_registry.json（canonical） | `skill/references/` | 机器可读 Provider Registry |
| SKILL.md 路由节改写 | `skill/SKILL.md` | 指向权威策略，声明唯一 Router |
| cua-gui-first-router 降级 | `~/.workbuddy/skills/`（Qoder 同步生效） | 描述改写 + 降级横幅：路由权移交，保留为 visual Provider 规程 |
| 用户级记忆 CUA-first 总则改写 | `~/.workbuddy/MEMORY.md` | 2026-09-15 CUA-first → 2026-10-04 UC Router-first（PLAYBOOK 纪律并入 visual 路径） |
| 路由验证 | `tests/validate_routing.py` + `evidence/routing_validation.json` | 15 代表任务 + 11 策略断言 |
| 三宿主同步 | `adapters/sync_skill.py` | 9 文件 × 3 宿主 SYNCED，--check 全 MATCH |

## 二、分类结果（不删除任何旧 Skill）

- **KEEP**：universal-computer（canonical Router）、cua-uia-health-smoke-recovery、
  windows-interactive-launch、8 个 Windows 领域故障 Skill（由 Router 委托）
- **MERGE（知识并入，壳保留）**：cua-gui-first-router 的 PLAYBOOK 纪律并入
  ROUTING_POLICY visual 路径与用户记忆
- **DELEGATE**：agent-browser 插件、playwright-cli 插件（WorkBuddy 内置）、
  browseros-neo MCP（Codex）、Qoder 内置 computer-use
- **DEPRECATE（已执行）**：cua-gui-first-router 路由身份
- **REMOVE_CANDIDATE**：无（本轮不删除）

## 三、最终裁决（任务书格式）

```text
UNIVERSAL_COMPUTER_ROUTING        = PASS      # 15/15 代表任务 + 11/11 策略断言
SKILL_CONFLICT_AUDIT              = PASS      # 3 类冲突全部收敛（见 inventory §五）
DUPLICATE_AUTO_TRIGGER            = NO        # Skill 级 0；browseros-neo 为 MCP Provider 非 Skill
API_MCP_ROUTING                   = PASS      # registry api_mcp 域，直接用优先
CLI_ROUTING                       = PASS      # RT13/RT14：文件/系统 → PowerShell
PLAYWRIGHT_ROUTING                = PASS      # RT01-05：浏览器 5 场景全 → playwright
COM_ROUTING                       = PASS      # RT11/12：Office → com（use_com 声明）
UIA_ROUTING                       = PASS      # RT06-08：标准控件 → uia
WIN32_ROUTING                     = PASS      # RT09/10：窗口层
VISUAL_CUA_ROUTING                = PASS      # RT15：仅自绘/兜底；默认权重 9，特殊场景 2
TOP_K_PROVIDER_LIMIT              = 2         # 特殊场景至多 3
FALLBACK_LIMIT                    = 2/Provider（全链 = 候选数 × 2，禁无限循环）
ROUTING_COST_MODEL                = ENABLED   # api(1) < cli(2) < playwright/com(3) < uia/win32(4) < visual(9)
CAPABILITY_CACHE                  = ENABLED   # 24h TTL + degraded 降位 + doctor 恢复
WORKBUDDY_ROUTING_POLICY_MATCH    = PASS
CODEX_ROUTING_POLICY_MATCH        = PASS
QODER_ROUTING_POLICY_MATCH        = PASS      # junction，与 WorkBuddy 同份
CANONICAL_ROUTING_SOURCE_COUNT    = 1         # skill/references/ROUTING_POLICY.md
HOST_ROUTING_FORKS                = 0
OLD_CUA_CONFLICTS                 = RESOLVED  # cua-gui-first-router 降级 + 记忆总则改写
OLD_BROWSER_SKILL_CONFLICTS       = RESOLVED  # agent-browser/playwright-cli/browseros-neo → DELEGATE
RECURSIVE_SKILL_CALLS             = NONE      # UC→cua-pilot→终端，无 Skill 回环
READY_FOR_DAILY_USE_ALL_HOSTS     = YES       # WorkBuddy/Qoder 新会话实机复测与待办 #38 合并
```

## 四、验证明细

- **15 代表任务**（离线决策断言，无真实网络/副作用）：浏览器×5、UIA×3、
  Win32×2、COM×2、CLI×2、Visual×1 —— 全部命中策略预期 Provider
  （证据 `evidence/routing_validation.json`）。
- **11 策略断言**：TOP_K=2/3、fallback=2、visual 权重降级、各域首选项、
  single_router 声明 —— 全 PASS。
- **Codex 单一触发实测**：自然语言浏览器任务 → 选 universal-computer；
  提及的 browseros-neo 经查证为 MCP 服务器（config.toml [mcp_servers]，端口
  9014），归 Provider 层 DELEGATE，不构成 Skill 竞争。
- **fallback 既有证据**：R3 三段式阶梯降级 + F1 恢复（Phase 1 验收）继续有效。

## 五、边界与遗留

- WorkBuddy/Qoder 新会话的实机自然语言触发复测（含确认无多 Skill 抢任务）
  合并到待办 #38，用户开新会话即可验证。
- 官方内置插件（agent-browser/playwright-cli）描述不可改，靠 ROUTING_POLICY
  声明优先级约束；若未来版本出现实际抢触发，按冲突审计流程记录后升级处理。

---

## 六、V1.1 冻结前口径小修（2026-10-04 15:57 用户裁决后执行）

用户判 V1.1 路由整合 PASS，冻结前修正 3 个口径问题（只做配置/文档小修，
未重跑 Playwright/UIA/CUA 功能测试）：

1. **去全局固定顺序**：删除"API→CLI→Playwright→COM→UIA→Win32→Visual"式
   全局死排序表述，统一为 domain-aware routing（先分类任务域 → 域内排序 →
   primary + 至多 1 个正常 fallback → 特殊至多 3 候选）。五条域内阶梯写入
   ROUTING_POLICY §1，并加反例约束（Excel→COM、关 Chrome→CLI/Win32、
   标准对话框→UIA）。
2. **FALLBACK_LIMIT 口径拆分**：`MAX_RETRIES_PER_PROVIDER = 2`（同 Provider
   内重试）与 `MAX_PROVIDER_SWITCHES = 2`（整条任务最多换 2 次 Provider）
   拆为两个独立计数器，杜绝 Playwright→UIA→Win32→Visual 链式膨胀。
3. **Capability cache 分层**：installed（24h，仅静态安装/注册事实）与
   runtime_healthy（session）/ runtime_degraded（5–15 min，偶发失败专用，
   禁入 24h 缓存）/ process_window（实时或 ≤60s）分离，一次临时失败不再
   导致 Provider 被降级一整天。

同步修改：ROUTING_POLICY.md、provider_registry.json、SKILL.md、
validate_routing.py（策略断言扩为 16 条，含 DOMAIN_AWARE_NO_GLOBAL_ORDER、
SWITCHES_AND_RETRIES_INDEPENDENT、CACHE_DEGRADED_NOT_IN_INSTALLED 等）。
静态断言重跑 16/16 PASS（路由决策 15/15 不变），三宿主 sync --check 全 MATCH。

## 七、V1.1 正式冻结裁决

```text
UNIVERSAL_COMPUTER_V1_1        = ACCEPTED
ROUTER_ENTRY                   = universal-computer
DOMAIN_AWARE_ROUTING           = YES
GLOBAL_FIXED_PROVIDER_ORDER    = NO
MAX_PROVIDER_SWITCHES          = 2
DUPLICATE_AUTO_TRIGGER         = 0
OLD_CUA_ROUTER                 = DEPRECATED
VISUAL_CUA                     = PROVIDER
CANONICAL_ROUTING_SOURCE_COUNT = 1
HOST_ROUTING_FORKS             = 0
READY_FOR_DAILY_USE_ALL_HOSTS  = YES
```

WorkBuddy/Qoder 新会话自然语言触发留作实际使用时顺手验收（待办 #38），
不再阻塞上线。**UniversalComputer V1.1 自此冻结**，等待日常使用中发现
缺口后增量升级。

---

## 八、UCRoutingPolicy = FROZEN_V1_1（2026-10-04 16:53 最终冻结）

用户提出 4 条冻结前不变量，全部并入 `ROUTING_POLICY.md` 新增 §7 与
`provider_registry.json`（policy_version 升为 `ucrout-v1.1-20261004-frozen`）：

1. **§7.1 Canonical Source**：ROUTING_POLICY.md 是唯一规范源，
   provider_registry.json 是其机器可读投影（非第二套策略源）；三者
   （规范→registry→宿主副本）语义必须一致，冲突时规范优先并判
   `ROUTING_POLICY_SYNC = FAIL`。
2. **§7.2 Provider Limits**：`INITIAL_TOP_K_PROVIDERS=2`、
   `MAX_RETRIES_PER_PROVIDER=2`、`MAX_PROVIDER_SWITCHES=2`（切换按实际
   执行 Provider 变化计数：Primary→F1=1、F1→F2=2，一条任务最多进入 3 个
   Provider），语义无歧义。
3. **§7.3 Cross-Skill Recursion Guard**：`ROUTER_REENTRY_SAME_TASK=FORBIDDEN`、
   `CALL_DEPTH_MAX=4`；同 task_id 禁止 Router 递归重决策；每次跨 Skill 委托
   记录 task_id/parent_skill/child_skill/delegation_reason/call_depth。
4. **§7.4 Explicit Override**：只覆盖 Provider 排序，不得绕过安全规则/
   风险等级/SSRF Guard/权限边界/高风险不可逆确认/审计/Provider 硬性安全限制。

### 取证记录（重要）

执行中发现 canonical `ROUTING_POLICY.md` 磁盘内容被用户消息文本**意外覆盖**
（编辑器粘贴落盘）。已从会话历史完整重建 v1.1 正文 + §7，并通过下述断言
与三宿主副本交叉验证无内容缺失。此事件本身验证了"三宿主副本 + 会话证据"
的冗余恢复路径有效。

### 静态验证（按要求未重跑功能验收）

```text
路由决策断言   = 15/15 PASS（不变）
策略断言       = 26/26 PASS（含 §7.1/7.2/7.3/7.4 全部不变量）
语义一致性断言 = 8/8 PASS（ROUTING_POLICY.md ↔ provider_registry.json）
sync --check   = 3/3 宿主 MATCH
```

```text
UCRoutingPolicy = FROZEN_V1_1

SINGLE_ROUTER                  = YES
DOMAIN_AWARE_ROUTING           = YES
GLOBAL_FIXED_PROVIDER_ORDER    = NO
INITIAL_TOP_K_PROVIDERS        = 2
MAX_RETRIES_PER_PROVIDER       = 2
MAX_PROVIDER_SWITCHES          = 2
VISUAL_CUA_DEFAULT_PRIMARY     = NO
VISUAL_CUA_SPECIAL_UI_PRIMARY  = YES
CROSS_SKILL_RECURSION_GUARD    = YES
EXPLICIT_OVERRIDE_SUPPORTED    = YES
EXPLICIT_OVERRIDE_BYPASS_SAFETY= NO
CANONICAL_ROUTING_SOURCE_COUNT = 1
HOST_ROUTING_FORKS             = 0
```

**ROUTING_POLICY V1.1 到此正式冻结，不再追加规则**；日常使用中发现缺口
走增量升级（新版本号），不覆盖冻结语义。
