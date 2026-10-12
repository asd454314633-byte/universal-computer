# 01_ARCHITECTURE.md — Universal Computer Core 架构

## 定位

一套与任何 Agent 宿主（WorkBuddy / Codex / Qoder CN / 未来其他）解耦的通用电脑操作核心。
Core 不知道调用方是谁；宿主只通过 CLI 或 factory 接口使用它。

## 执行能力阶梯（冻结）

```
任务 → 能力路由
  ① 原生 API / MCP
  ② Playwright（浏览器主路径）
  ③ Windows UIA / Win32 / COM（桌面主路径）
  ④ Visual CUA（唯一视觉兜底，默认关闭）
```

结构化手段（DOM / Accessibility Tree / UIA / COM / Win32）永远优先于视觉坐标点击。

## 目录

```
core/      protocol(统一结果协议) router(能力路由) runner(任务执行)
           state(状态机) security(风险分级) audit(审计) recovery(恢复)
providers/ browser/playwright  windows/{uia,win32,com}
           mcp(探测槽位) webmcp(实验性探测,默认关) visual(可插拔接口+Mock)
cli/       main.py —— argparse 统一入口
factory.py 唯一组合根：宿主/适配器只调用 build_router / build_runner
skill/     SKILL.md（无宿主绑定）
tests/     最小真实验收 + 隔离 fixture
evidence/  测试证据(JSON/截图) + 审计 JSONL
logs/      任务状态持久化
```

## 关键设计决定

| 决定 | 理由 |
|---|---|
| Python 单实现 | UIA(uiautomation)+Win32(pywin32)+COM(win32com)+Playwright 一栈打通，依赖最小 |
| Playwright 用本机 Chrome channel | 不强制下载 Chromium；attach/persistent profile 均支持 |
| 桌面用 uiautomation 库 | 成熟库复用；不做 UIA COM 绑定的重复造轮 |
| COM 仅接口+注册表探测 | Phase 1 无 Office 操作需求；避免侵入性 Dispatch |
| Visual 仅接口+Mock | 不绑定任何视觉模型；接口稳定后可接 Fara/UI-TARS 等 |
| 所有动作返回 ActionResult | 失败必须结构化（类型/阶段/可重试/可降级/原始异常），禁止裸 "失败" |

## 解耦保证

- Core 无任何宿主名称、宿主配置、宿主确认 UI。
- 确认回调由宿主经 `build_runner(confirm_callback=...)` 注入；Core 只声明风险等级。
- 删除 MCP / WebMCP / UFO²(未引入) / Stagehand(未引入) 任一模块，Core 照常运行。
