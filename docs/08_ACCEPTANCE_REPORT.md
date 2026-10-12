# 08_ACCEPTANCE_REPORT.md — Phase 1 最终验收报告

日期：2026-10-03 ｜ 环境：Windows 11 ｜ Python 3.13.14（隔离 venv）

## 一、最小真实验收明细（tests/run_acceptance.py，最终回归）

| 用例 | 内容 | 结果 | 证据 |
|---|---|---|---|
| B1 | 打开网页读取 `#page-title` | PASS | evidence/B1_open_read.json |
| B2 | 结构定位输入框填写并回读 | PASS | evidence/B2_fill_input.json |
| B3 | 结构定位按钮点击，状态文本变化 | PASS | evidence/B3_click_button.json |
| B4 | 布局+DOM 层级扰动后仍按结构完成 | PASS | evidence/B4_layout_change.json |
| W1 | 识别自有 fixture 真实窗口 | PASS | evidence/W1_recognize_window.json |
| W2 | 读取 UIA 控件树（Edit/Button） | PASS | evidence/W2_read_tree.json |
| W3 | set_text→回读一致；invoke 按钮状态变化 | PASS | evidence/W3_control_action.json |
| W4 | 零坐标证明（仅结构属性定位） | PASS | evidence/W4_no_coordinates.json |
| R1 | 浏览器任务路由至 playwright | PASS | evidence/R1_route_browser.json |
| R2 | 标准控件任务路由至 uia | PASS | evidence/R2_route_windows.json |
| R3 | 结构化不可用才允许 visual 兜底（三段式） | PASS | evidence/R3_fallback_order.json |
| F1 | 无效 Selector→重获取→重定位→恢复，共 2 次 | PASS | evidence/F1_recovery.json |

汇总：`evidence/acceptance_summary.json` → OVERALL: PASS (12/12)
审计：`evidence/audit/2026-10-03.jsonl`（每个真实动作一行 JSONL）

## 二、验收结果格式（任务第二十三节）

```text
UNIVERSAL_CORE                 = PASS
PLAYWRIGHT_PROVIDER            = PASS
WINDOWS_UIA_PROVIDER           = PASS
WIN32_SUPPORT                  = PARTIAL   # 窗口枚举/聚焦/消息路径可用并经实测；
                                            # 完整窗口管理层未在 Phase 1 范围
COM_PROVIDER_INTERFACE         = PASS      # 契约+注册表探测；未绑定具体应用
VISUAL_PROVIDER_INTERFACE      = PASS      # 接口+Mock；未绑定任何视觉模型
CAPABILITY_ROUTER              = PASS
FAILOVER                       = PASS      # R3 阶梯降级三段式验证
RECOVERY                       = PASS      # F1 验证，硬上限 2 次尝试
AUDIT_LOG                      = PASS      # JSONL 逐动作审计，证据封顶保存
UNIVERSAL_CLI                  = PASS      # capabilities/doctor/run/browser/windows/inspect 实测
UNIVERSAL_SKILL                = PASS      # skill/SKILL.md 宿主中立完成

WORKBUDDY_DEPENDENCY           = NO
CODEX_DEPENDENCY               = NO
QODER_CN_DEPENDENCY            = NO
OPENCLAW_DEPENDENCY            = NO

READY_FOR_AGENT_ADAPTER_PHASE  = YES
```

## 三、裁决条件核对（第二十四节）

- Universal Core 独立运行：是（无宿主 import、无宿主确认 UI、确认经回调注入）
- 浏览器主路径通过：是（B1-B4，Playwright 1.55.0 + Chrome channel）
- Windows UIA 主路径通过：是（W1-W4，uiautomation 2.0.29）
- 路由与 fallback 通过：是（R1-R3）
- CLI 可独立调用：是（任何能启动进程并解析 JSON 的调用方即可用全系统）
- 通用 Skill 完成：是（skill/SKILL.md，10 项要求全覆盖，无宿主名）
- 无 Agent 宿主硬依赖：是（代码库 grep 无 WorkBuddy/Codex/Qoder/OpenClaw 引用）

## 四、版本锁定

playwright==1.55.0 ｜ uiautomation==2.0.29 ｜ comtypes==1.4.17 ｜
pywin32==312 ｜ greenlet==3.5.6 ｜ pyee==13.0.1
（升级须重跑 run_acceptance.py 全 PASS 后晋升）

## 五、过程中发现并修复的真实缺陷（对架构有价值的教训）

1. **UIA 全局搜索污染**：带 control_type 的搜索最初从桌面根发起，
   曾误中系统托盘按钮"显示隐藏的图标"。已修复为强制窗口作用域内定位
   （这是安全属性，不只是 bug）。
2. **Notepad 会话复用风险**：首轮 W 测试用记事本做 fixture，Win11 记事本
   进程复用导致匹配到已打开的用户文档窗口。已改为自有 Win32 fixture 窗口
   （唯一类名），并确立纪律：**桌面测试只使用自有隔离窗口**。
   该轮交互未触发任何保存，磁盘文件无改动；无记事本窗口残留（已复核）。
3. **经典 Win32 控件的模式差异**：MSAA 桥接的 ValuePattern void 返回、
   GetClickablePoint 可能为 None。建立三级降级：
   UIA Pattern → WM 消息(hwnd) → 键盘/可点击点，全部记录 method。

## 六、Phase 1 明确不做（第二十一节遵守情况）

未测试多网站/多软件、未比较视觉模型、未引入 Stagehand/UFO²/WebMCP 依赖、
未建三套 Adapter、未修改任何现有生产项目。
