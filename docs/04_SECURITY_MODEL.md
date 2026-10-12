# 04_SECURITY_MODEL.md — 安全与权限

## 三级动作风险

| 级别 | 含义 | 示例 |
|---|---|---|
| READ | 只读 | 浏览、读文本、截图、快照、列窗口、读控件树 |
| WRITE | 可写 | 输入文字、填表、点击、上传、保存文件、invoke |
| DESTRUCTIVE | 破坏性 | 删除、覆盖、支付、不可逆提交、改系统、对外发送、杀进程 |

## 职责边界（冻结）

- **Core 只声明风险**：`core.security.classify(action)` 返回 `RiskDecision`。
- **确认权在宿主**：宿主经 `build_runner(confirm_callback=...)` 注入回调；
  WRITE/DESTRUCTIVE 动作会先询问回调，拒绝则返回 `PERMISSION_DENIED`，Core 不弹任何 UI。
- 任务可用 `risk` 字段**上调**（不得下调）某步骤等级，如把 `click` 声明为 DESTRUCTIVE。

## 定位纪律（安全属性）

- UIA 搜索永远限定在目标窗口作用域内（实测教训：全局搜索曾误中系统托盘按钮）。
- 浏览器动作基于 DOM 选择器；桌面动作基于 UIA 结构属性 / hwnd 消息。
- 桌面 fixture 测试使用自有窗口，禁止把按键注入用户真实会话。
