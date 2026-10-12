# UniversalComputer（通用电脑操控系统）

与任何 Agent 宿主解耦的通用电脑操作核心：把「操作浏览器、Windows 桌面软件、
窗口控件、命令行」的能力收敛为一套**宿主中立**的 CLI + JSON 协议。
任何能「启动进程 + 解析 JSON」的 Agent（WorkBuddy / Codex / 自研脚本均可）
都可以调用它，无需绑定特定宿主。

- 许可证：MIT（自研代码，见 `LICENSE`）；第三方依赖出处见 `THIRD_PARTY_NOTICES.md`
- 平台：Windows 10/11，Python 3.11+（3.13 验证）
- 形态：纯 Python 代码库 + 可选的 Agent Skill 包（`skill/`），无服务、无后台驻留

## 能力范围

| 域 | 主路径 | 覆盖能力 |
|---|---|---|
| 浏览器 | Playwright（结构化 DOM） | 打开/读文本/填表/点击/截图/无障碍快照/多标签页/上传下载/iframe/dialog；支持 attach 已运行浏览器（CDP）、持久登录 Profile |
| Windows 桌面 | UIA（控件树/Pattern） | 列窗口、读控件树、按 AutomationId/Name/ControlType/ClassName 定位、invoke、set_text、get_value、focus；动作链 Pattern → WM 消息 → 键盘 |
| Windows 窗口层 | Win32（hwnd/消息） | 枚举窗口、聚焦激活、前台窗口查询 |
| Office / 原生接口 | COM（注册表探测 + 晚绑定调用） | ProgID 探测、`dispatch_com` 晚绑定分发 |
| 视觉兜底 | 可插拔 `VisualProvider` 接口 | `observe/locate/click/type/drag/scroll/verify` 契约 + Mock 实现（不绑定具体模型，默认关闭） |
| MCP | 接口预留 | 宿主注册 MCP server 的探测槽位（Phase 1 不含传输实现） |

工程能力：能力探测（`detect`）、Domain-aware 路由、声明式多步任务（`uc.py run`）、
失败恢复（重获取→重定位，硬上限 2 次）、任务状态机与断点续跑判定、逐动作 JSONL
审计、三级风险声明（READ / WRITE / DESTRUCTIVE）。

## 安装

```powershell
# 1. 创建隔离 venv（路径可自定义）
python -m venv <venv-dir>
# 2. 安装锁定版本依赖
<venv-dir>\Scripts\python.exe -m pip install -r requirements.lock.txt
# 3. 健康检查（需要本机 Chrome；Playwright 默认走 channel="chrome"）
cd UniversalComputer
<venv-dir>\Scripts\python.exe uc.py doctor
```

`doctor` 输出各 Provider 可用性与浏览器实启结果。全部 `available: true` 且
`browser_live_launch: true` 即安装成功。详见 `INSTALL.md`。

## 调用

统一入口 `uc.py`，stdout 恒为单个 JSON 文档：

```bash
python uc.py doctor                          # 健康检查
python uc.py capabilities                    # 各 Provider 可用性
python uc.py run task.json                   # 声明式多步任务
python uc.py browser open --url https://example.com
python uc.py browser fill --selector "#q" --value "hello"
python uc.py windows list
python uc.py windows read_tree --window-name "记事本" --depth 4
python uc.py inspect window --name "记事本"  # 只读侦察
```

全局参数：`--headed`（前台浏览器）、`--profile <dir>`（持久登录态）、
`--cdp <endpoint>`（attach 已运行浏览器）、`--webmcp`（实验性探测，默认关）、
`--visual`（允许视觉兜底，默认关）。完整动作清单与返回契约见
`skill/references/PROVIDERS.md`。

### 声明式任务

```json
{
  "task_id": "example-task",
  "domain": "browser",
  "steps": [
    {"step_id": "s1", "action": "open", "params": {"url": "https://example.com"}},
    {"step_id": "s2", "action": "read_text", "params": {"selector": "h1"}}
  ]
}
```

### 作为 Agent Skill 使用

`skill/` 是宿主中立的 Agent Skill 包（SKILL.md + references + scripts）。
定位 Core 的顺序：环境变量 `UNIVERSAL_COMPUTER_HOME` → Skill 目录下
`scripts/core_path.txt`（由 `adapters/sync_skill.py` 同步时生成）→ 手动指定。
可用 `python adapters/sync_skill.py --check` 校验宿主副本一致性。

### 作为库使用

```python
from factory import build_router, build_runner   # 唯一组合根
router, providers = build_router()
runner = build_runner(router)
```

## 路由策略（摘要）

先探测、后路由；**不存在全局固定 Provider 顺序**——先分类任务域，再在域内按
可靠性/成本选 1 个 primary + 至多 1 个正常 fallback（特殊至多 3 候选）：

```
browser: (webmcp, opt-in) → playwright → visual(仅 --visual)
windows: com(任务声明 use_com 时) → uia → win32 → visual(仅 --visual)
```

重试与切换是独立计数器（同 Provider 内重试 ≤ 2；整条任务最多换 2 次 Provider），
禁止链式膨胀。完整策略见 `skill/references/ROUTING_POLICY.md` 及其机器可读投影
`skill/references/provider_registry.json`。

## 测试

```bash
python tests/run_acceptance.py    # 最小真实验收：浏览器/路由/恢复/Windows UIA（自有 fixture）
python tests/validate_routing.py  # 路由收敛离线断言（无网络、无副作用）
```

测试使用自有的本地 fixture 站点与自建 Win32 窗口，不触碰用户真实应用会话。
升级任何依赖前必须重跑验收并全部 PASS。

## 目录结构

```
uc.py                  # 启动器
factory.py             # 组合根：provider 装配 + router + runner
cli/                   # CLI 入口（所有子命令输出单个 JSON）
core/                  # router / runner / protocol / security / recovery / state / audit
providers/             # browser(playwright, webmcp) / windows(uia, win32, com) / visual / mcp
skill/                 # 宿主中立 Agent Skill 包（SKILL.md + references + scripts）
adapters/              # 宿主 Skill 同步器（sync_skill.py）
tests/                 # 验收测试 + 隔离 fixture
docs/                  # 架构 / Provider 契约 / 安全模型 / 验收报告等设计文档
requirements.lock.txt  # 依赖锁定
```

## 已知限制

1. **仅支持 Windows**（UIA / Win32 / COM 依赖 Windows API）；浏览器部分跨平台可跑，
   但整体面向 Windows 场景设计与验证。
2. **Visual Provider 仅为接口 + Mock**：未内置任何视觉模型，`--visual` 开启后
   也只有契约与模拟实现，不会真正操作屏幕。接入真实模型需自行实现
   `VisualProvider` 子类。
3. **MCP Provider 仅为探测槽位**：Phase 1 不含 MCP 传输实现。
4. **WebMCP 为实验性探测**：默认关闭，探测结果仅供参考，永不阻断任务。
5. **COM Provider 为接口 + 注册表探测**：具体应用的 COM 操作需按应用编写
   adapter（Office 等），核心不内置逐应用 COM 语义。
6. **风险确认不在 Core 内**：Core 只声明风险等级（DESTRUCTIVE 默认返回
   `PERMISSION_DENIED`），是否确认由调用宿主决定。
7. **依赖版本已锁定**：升级依赖前必须重跑 `tests/run_acceptance.py` 全部 PASS。
8. 运行时会生成 `logs/`（任务状态）与 `evidence/`（审计日志），已在 `.gitignore`
   中排除；请按需自行清理。

## 许可证

- 自研代码：MIT（`LICENSE`）
- 第三方依赖：均通过 pip 安装，未修改、未内联；出处与许可见
  `THIRD_PARTY_NOTICES.md`
