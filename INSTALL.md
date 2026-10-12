# INSTALL.md — 安装 / 卸载 / 健康检查

## 依赖

- Windows 10/11
- Python 3.11+（已在 3.13 验证）
- 本机 Chrome（Playwright 走 `channel="chrome"`；如需 Chromium 可另行 `playwright install chromium`）

## 安装（隔离 venv，推荐）

```powershell
# 1. 创建 venv（示例路径，可自定义）
python -m venv <venv-dir>
# 2. 安装锁定版本
<venv-dir>\Scripts\python.exe -m pip install -r requirements.lock.txt
# 3. 健康检查
cd UniversalComputer
<venv-dir>\Scripts\python.exe uc.py doctor
```

`doctor` 返回各 Provider 可用性和浏览器实际启动结果。验证浏览器能力时，
检查 `capabilities.playwright: true` 与 `browser_live_launch: true`；
验证 Windows 控件操作时，检查 `capabilities.uia: true`（窗口层可另查 `win32`）。
`mcp`、`webmcp` 和 `visual` 等可选/占位 Provider 不要求全部为 `true`。
`doctor` 只做环境探测，不等于全部实际操作任务已经验收。

## 版本锁定

`requirements.lock.txt` 为实测锁定（playwright==1.55.0, uiautomation==2.0.29,
comtypes==1.4.17, pywin32==312 等）。升级任何依赖前必须重跑
`python tests/run_acceptance.py` 并全部 PASS 后才可晋升。

## 卸载

1. 删除项目目录 `UniversalComputer/`（证据、日志、状态一并清除）。
2. 删除安装时创建的 venv 目录。
3. 无全局污染：所有依赖只存在于 venv 内；无注册表/服务/计划任务写入；
   无浏览器配置修改（`--profile` 指定的目录随项目删除）。
