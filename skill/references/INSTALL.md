# INSTALL.md — 安装 / 依赖 / 宿主分发

## 依赖

- Windows 10/11；Python 3.11+（3.13 验证）
- 本机 Chrome（Playwright 走 `channel="chrome"`）
- 依赖锁定 `requirements.lock.txt`（playwright==1.55.0, uiautomation==2.0.29,
  comtypes==1.4.17, pywin32==312 等）

## 安装后配置（二选一）

1. 设置环境变量 `UNIVERSAL_COMPUTER_HOME` 指向 Core 目录（推荐，显式且可迁移）；
2. 或运行 `python adapters/sync_skill.py`，由同步器把 Core 绝对路径写入
   各宿主副本的 `scripts/core_path.txt`（仓库内的该文件默认为空，
   同步时自动生成，不提交具体机器路径）。

Python 解释器解析顺序：环境变量 `UNIVERSAL_COMPUTER_PYTHON` → PATH 中的
`python`。如需指定 venv，设置 `UNIVERSAL_COMPUTER_PYTHON` 即可。

## 健康检查

```bash
python uc.py doctor          # 全部 available:true 且 browser_live_launch:true 即正常
python uc.py capabilities
```

## 新机安装

```powershell
python -m venv <venv-dir>
<venv-dir>\Scripts\python.exe -m pip install -r requirements.lock.txt
<venv-dir>\Scripts\python.exe uc.py doctor
```

升级任何依赖前必须重跑 `tests/run_acceptance.py` 全 PASS。

## 宿主分发（canonical → 三宿主）

canonical 唯一源 = `UniversalComputer/skill/`。
宿主副本由 `adapters/sync_skill.py` 生成，**禁止在宿主副本上手工修改**：

```bash
python adapters/sync_skill.py            # 同步到全部三个宿主
python adapters/sync_skill.py --target workbuddy   # 仅一个
python adapters/sync_skill.py --check    # 只校验一致性
```

| 宿主 | 安装位置 |
|---|---|
| WorkBuddy | `~/.workbuddy/skills/universal-computer/` |
| Qoder CN | `~/.qoder-cn/skills/`（实测是指向 `~/.workbuddy/skills` 的 junction，同步一次即两宿主生效） |
| Codex | `~/.codex/skills/universal-computer/` |

同步器会把 Core 绝对路径写入副本的 `scripts/core_path.txt`；
Core 移动/重命名后重跑同步即可。

## 卸载

1. 删除三个宿主 skills 目录下的 `universal-computer/`
2. 删除 Core 目录与 venv
3. 无全局污染：依赖只在 venv 内；无注册表/服务/计划任务写入
