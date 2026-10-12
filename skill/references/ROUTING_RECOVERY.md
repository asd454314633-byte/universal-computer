# ROUTING_RECOVERY.md — 执行路由架构与恢复机制

## 路由架构

```
任务
 │
 ▼
现成 API / MCP / CLI？ ── YES → 直接使用
 │ NO
 ▼
浏览器任务？ ── YES → Playwright
 │ NO
 ▼
Windows 软件？
 ├─ COM（应用有成熟接口时优先）
 ├─ UI Automation（控件树/Pattern）
 ├─ Win32（HWND/消息/键鼠）
 └─ 键盘鼠标
 │
 ▼
结构化能力无法完成
 │
 ▼
Visual CUA（仅 --visual 开启时）
```

路由决策由 Core 的 `CapabilityRouter` 完成（`uc.py run` 的 `domain: "auto"`），
Agent 不需要手工挑 Provider；只在必要时用 step 的 `provider` 字段钉死。

各域内部优先级：

```
browser: (webmcp, opt-in) → playwright → visual(仅 --visual)
windows: com(声明时) → uia → win32 → visual(仅 --visual)
```

## 恢复机制

```
识别失败
↓
重新观察（inspect / 重新 snapshot）
↓
重定位
↓
重试（硬上限 2 次，禁止无限循环）
↓
必要时切 Provider（degrade_allowed 时按阶梯降级）
```

典型切换：

| 场景 | 动作 |
|---|---|
| Playwright selector 失效 | 重新 snapshot → 修 selector 重试 |
| DOM 不可访问（SPA 反爬/无 DOM） | 切 UIA / Win32 / Visual |
| UIA 控件不可见 | Win32 消息 / 键盘输入 → Visual |
| CLI 更简单可靠 | 直接切 CLI |
| Provider 依赖缺失 | `uc.py doctor` 诊断，按 INSTALL.md 修复 |

## 失败识别

错误 JSON 恒带结构化 `error.type`：

- `LOCATE_FAILED`（retryable=true）：修正定位条件后重试；Core 已自动做
  过一次"重获取状态→重定位"。
- `PROVIDER_UNAVAILABLE`：`doctor` 检查；按 INSTALL.md 安装依赖。
- `PERMISSION_DENIED`：DESTRUCTIVE 动作未确认；宿主确认后带 `risk`
  覆盖重发。
- `TIMEOUT`：目标加载慢；先 `inspect` 确认目标存在，或加大超时。
- `RUNTIME_ERROR`：看 `error.raw`；必要时换路径。

连续失败 2 次后不要再原样重试——换 Provider 或换任务表述。
