# 02_PROVIDER_CONTRACT.md — Provider 统一契约

## 接口

```python
class BaseProvider(ABC):
    name: str          # 逻辑名，路由表用它寻址（如 "playwright" / "uia" / "visual"）
    domain: str        # browser | windows | visual | mcp

    detect() -> CapabilityInfo       # 便宜的可用性探测，无副作用
    refresh_state()                  # 恢复钩子：重获取页面/窗口状态
    close()                          # 释放会话资源
    dispatch(action, params) -> ActionResult   # 所有动作统一入口
```

## 统一结果结构

```json
{
  "success": true,
  "provider": "playwright",
  "action": "click",
  "target": {"selector": "#submit"},
  "result": {"clicked": "#submit"},
  "evidence": [],
  "duration_ms": 42,
  "error": null,
  "recovered": false
}
```

失败时 `error` 必填：

```json
{"type": "LOCATE_FAILED", "phase": "locate",
 "retryable": true, "degrade_allowed": true, "raw": "..."}
```

错误类型枚举：`PROVIDER_UNAVAILABLE | LOCATE_FAILED | TIMEOUT | PERMISSION_DENIED |
RUNTIME_ERROR | UNSUPPORTED_ACTION`。阶段：`detect | locate | execute | verify`。
禁止返回裸 `{"failed": true}`。

## 各 Provider 动作清单

| Provider | 动作 |
|---|---|
| playwright | open read_text fill click snapshot screenshot list_tabs switch_tab upload close evaluate |
| uia | list_windows read_tree find_control invoke set_text get_value focus |
| win32 | list_windows focus get_foreground |
| com | detect_progid dispatch_com |
| visual | observe locate click type drag scroll verify（接口约定） |

## 降级纪律

- UIA 控件动作内部按 `结构 Pattern → WM 消息(hwnd) → 键盘` 降级，全部记录 `method`。
- 跨 Provider 降级只由 Router 决定，Provider 自身不得私下换路径。
- 定位永远用 AutomationId / Name / ControlType / ClassName / 层级；
  绝对屏幕坐标不是合法主定位方式。
