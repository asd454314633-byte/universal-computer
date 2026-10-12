# Universal Computer — 自主开发与第三方开源依赖声明

**项目：** Universal Computer（通用电脑操控系统）  
**公开仓库：** https://github.com/asd454314633-byte/universal-computer  
**声明日期：** 2026-10-12

## 一、自主开发声明

Universal Computer 是本项目开发者自主开发、整合并维护的 Windows Agent 电脑操作项目。本仓库公开的主要工程实现包括：

- 宿主中立的命令行与 JSON 调用接口；
- 统一任务路由（Router）与 Provider 组合、操作结果协议；
- 浏览器、Windows UI Automation、Win32、COM 等接口的项目适配代码；
- 声明式任务执行、失败恢复、状态管理、风险分级和审计记录；
- 通用 Agent Skill、宿主同步工具以及相关配置、示例、测试和文档。

上述声明指本仓库中由本项目完成的**具体软件实现与整合工作**，并非宣称独立发明浏览器自动化、Windows 控件自动化、计算机使用 Agent、MCP 或其他通用技术思想。

## 二、第三方技术与代码边界

项目通过标准公开 API 调用第三方开源库；当前公开仓库不捆绑所列第三方依赖包的源码。这些依赖由使用者按照 `requirements.lock.txt` 安装，其名称、来源及许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目在设计过程中研究并参考过其他电脑操作、浏览器自动化和 Agent 工程方案。**技术研究、方案比较及使用通用接口，不等于声称拥有那些上游项目的代码或版权。** 本声明不覆盖第三方已有的版权、商标、许可证或其他权利。

本仓库中的 Visual Provider 目前是接口与模拟实现，MCP Provider 目前是预留接口；不将这些部分描述为已经自研完成的真实视觉模型或完整 MCP 传输实现。

## 三、开放使用与署名

对本项目拥有授权权利的自研代码，依照仓库 [MIT LICENSE](LICENSE) 免费开放使用、复制、修改与再分发，包括商业使用。使用者应遵守该许可证所要求的版权和许可声明保留条件。

第三方依赖仍适用其**各自的许可证**，不因本项目采用 MIT 而变为本项目原创或被重新授权。

欢迎在遵守许可条件的前提下学习、复用、移植和改进本项目。若发现需要更正的来源或版权信息，可通过仓库 Issue 提出并附上具体文件与证据。

---

**English summary:** Universal Computer is an independently developed and maintained integration project. Its project-specific routing, CLI, provider adapters, Skill package, and supporting code are made available under the MIT License to the extent the project has rights to license them. It uses third-party open-source libraries through their public APIs; those libraries retain their own copyrights and licenses. This statement does not claim ownership of general computer-use techniques or upstream projects.
