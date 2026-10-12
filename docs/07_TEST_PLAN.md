# 07_TEST_PLAN.md — 最小真实验收计划

## 原则

避免为测试而测试。只做能证明架构成立的真实验收；不测几十个网站/软件，
不做大规模模型对比，不为证明功能大量调用云端模型。

## 环境

- 隔离 venv（managed Python 3.13），依赖锁定 `requirements.lock.txt`。
- 浏览器：本机 Chrome channel（headless）。
- 测试站点：`tests/fixtures/site/index.html` 经本地 HTTP 服务提供
  （含表单、按钮、布局+DOM 层级扰动脚本）。
- Windows fixture：`tests/fixtures/win32_host.py` 自有 Win32 窗口
  （唯一类名 `UcFixtureWnd`，标准 EDIT+BUTTON 控件）——零用户会话干扰。

## 用例

| 编号 | 内容 | 通过判据 |
|---|---|---|
| B1 | 打开网页并读取指定元素 | 读取到 `#page-title` 文本 |
| B2 | 结构定位输入框并填写 | 控件实际值等于写入值 |
| B3 | 语义/结构找按钮并点击 | 点击后状态文本变化 |
| B4 | 布局+DOM 层级变化后仍按结构完成操作 | 变更后 fill+click 仍成功 |
| W1 | 识别真实 Windows 窗口 | fixture 窗口出现在窗口列表 |
| W2 | 读取 UIA 控件树 | 树含 Edit/Button 节点 |
| W3 | UIA 找真实控件并执行动作 | set_text→get_value 回读一致；invoke 按钮后文本变"按钮已点击" |
| W4 | 证明非固定坐标 | 定位条件仅 ControlType/Name/ClassName，证据落盘 |
| R1 | 浏览器任务自动进 Playwright | RouteDecision.provider == playwright |
| R2 | 标准控件任务自动进 UIA | RouteDecision.provider == uia |
| R3 | 结构化不可用才允许 visual 兜底 | uia 禁→win32；全禁+visual 关→none；visual 开→visual |
| F1 | 人造无效 Selector | 失败→重获取状态→重定位→成功(recovered=true)，共 2 次尝试 |

## 证据

每个用例写 `evidence/<CASE>.json`；汇总写 `evidence/acceptance_summary.json`；
真实动作审计写 `evidence/audit/<date>.jsonl`。

## 运行

```bash
python tests/run_acceptance.py
```

退出码 0 = 全部 PASS。
