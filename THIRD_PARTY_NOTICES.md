# THIRD_PARTY_NOTICES.md — 第三方项目出处与许可

本仓库（Universal Computer Core 及其 Skill 包）为自研代码，采用 MIT 许可证
（见 `LICENSE`）。仓库**未内置、未修改、未再分发**任何第三方源码；下列第三方
开源项目仅作为**运行时依赖**通过标准包管理（pip）安装，本文件列出其出处与许可，
以满足署名要求。

| 项目 | 版本（锁定） | 许可证 | 项目地址 | 用途 |
|---|---|---|---|---|
| Playwright (playwright-python) | 1.55.0 | Apache-2.0 | https://github.com/microsoft/playwright-python | 浏览器结构化操作 Provider（主路径） |
| Python-UIAutomation-for-Windows (uiautomation) | 2.0.29 | Apache-2.0 | https://github.com/yinkaisheng/Python-UIAutomation-for-Windows | Windows UI Automation Provider |
| pywin32 | 312 | PSF License (Python Software Foundation License) | https://github.com/mhammond/pywin32 | Win32 窗口操作与 COM (`win32gui` / `win32com`) |
| comtypes | 1.4.17 | MIT | https://github.com/enthought/comtypes | COM 互操作支持库 |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | https://github.com/python-greenlet/greenlet | Playwright 的传递依赖 |
| pyee | 13.0.1 | MIT | https://github.com/jahyneal/pyee | Playwright 的事件发射器依赖 |

## 说明

1. 上表版本对应 `requirements.lock.txt` 的锁定版本；实际以各项目官方发布为准。
2. 本项目代码对上述库的调用均为其公开 API 的标准使用，未修改其源码，
   因此无需附带其源码或 NOTICE 文件全文；引用其公开 API 不改变其许可义务。
3. 本项目的 `visual` Provider 为可插拔接口（Phase 1 仅含接口与 Mock 实现），
   未绑定任何视觉模型；接入具体模型（如 OpenAI Computer Use / Fara / UI-TARS /
   Gemini Computer Use）时，请另行遵守相应模型服务的条款。
4. Playwright 需要浏览器二进制（Chrome/Chromium）。本项目默认使用本机已安装的
   Chrome（`channel="chrome"`）；亦可执行 `playwright install chromium` 安装
   Chromium。浏览器二进制受其各自许可约束，不在本仓库分发范围内。
5. 如你认为本文件存在遗漏或错误，请通过 GitHub Issues 联系维护者。
