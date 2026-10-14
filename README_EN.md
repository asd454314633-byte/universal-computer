# UniversalComputer — Windows Computer Use for AI Agents

**Host-independent Windows desktop and browser automation through a Python CLI and JSON interface.** Designed for agents that can launch processes and consume JSON output, including WorkBuddy, Codex, Qoder CN, and custom automation systems.

[中文说明](README.md) · [Windows install](INSTALL.md) · [Agent Skill](skill/SKILL.md) · [Acceptance report](docs/08_ACCEPTANCE_REPORT.md) · [Security model](docs/04_SECURITY_MODEL.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

## What does it do?

| Area | Implemented interface | Scope |
| --- | --- | --- |
| Browser automation | Playwright | DOM-based navigation, reading, form filling, clicks, accessibility inspection, screenshots, tabs, and Chrome/CDP attachment |
| Windows UI automation | Microsoft UI Automation (UIA) | Find windows and controls, inspect trees, invoke buttons, read and set values |
| Win32 | Window handles and messages | Window listing and activation, and a limited native fallback |
| COM | Discovery and late-binding | Interface provided; application-specific Office automation is not bundled |
| Visual automation | Provider contract + mock | **No real visual model bundled** |
| MCP | Detection slot | **No MCP transport server implemented in Phase 1** |
| Agent integration | CLI, JSON and optional Skill | No permanent background service or agent-host dependency |

The current scope is **Windows 10/11, Python 3.11+**, tested with Python 3.13. It is not a hosted cloud-computer service.

## Quick start — Windows PowerShell

Requires Git, Python and installed Chrome. Use an isolated Python environment; the commands below do not connect to a personal browser profile.

```powershell
git clone https://github.com/asd454314633-byte/universal-computer.git
cd universal-computer
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe uc.py doctor
.\.venv\Scripts\python.exe uc.py capabilities
```

To inspect supported commands, read [the Chinese README's CLI examples](README.md#调用). To install the optional agent-facing interface, read [skill/SKILL.md](skill/SKILL.md).

## Real acceptance scope

The published Phase 1 report records **12/12 passing tests** on the author's Windows test environment (October 3, 2026): four browser tests, four UIA tests, three routing tests and one recovery test. These used self-controlled fixtures and are **not** a claim of compatibility with every website, desktop app, or environment.

[Read the acceptance report](docs/08_ACCEPTANCE_REPORT.md) · [Provider architecture](docs/02_PROVIDER_CONTRACT.md) · [Recovery model](docs/05_RECOVERY_MODEL.md)

## Safety and current limits

- The core marks operations as READ / WRITE / DESTRUCTIVE, but permission and confirmation must be enforced by the host; destructive operations are denied by default.
- Real visual-screen control, an MCP transport server, and complete per-application COM adapters are **not** included.
- Local logs and evidence files are created during operation. Review them for sensitive data before sharing.
- Third-party Python packages are installed separately; the repository's original code is MIT licensed. See [LICENSE](LICENSE), [attribution](THIRD_PARTY_NOTICES.md), and the [development statement](ORIGINAL_DEVELOPMENT_STATEMENT.md).

## Project navigation

**[Installation](INSTALL.md)** · **[Architecture](docs/01_ARCHITECTURE.md)** · **[Routing](docs/03_ROUTER_DESIGN.md)** · **[CLI examples](README.md#调用)** · **[Tests](tests/run_acceptance.py)** · **[Agent Skill](skill/SKILL.md)** · **[Issues](https://github.com/asd454314633-byte/universal-computer/issues)**

This repository is an open-source automation core and a Phase 1 foundation—not a promise of unattended, unrestricted computer operation.
