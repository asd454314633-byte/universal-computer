# 06_SKILL_SPEC.md — Skill 规格

见 `skill/SKILL.md`（正文）。规格要点：

1. **能做什么**：浏览器结构化操作、Windows UIA/Win32 结构化操作、能力探测、
   声明式任务执行、恢复重试、审计。
2. **何时使用**：需要操作网页或 Windows 桌面程序，且调用方能启动进程并解析 JSON。
3. **何时不能**：目标应用既无 DOM/UIA/Win32 结构面、又未开启 visual 兜底时；
   需要 Core 未实现的原生 API 语义时。
4. **CLI 入口 / 参数 / 返回 JSON / 风险等级 / 常见失败 / Provider 优先级 / 调用实例**
   全部在 SKILL.md 中以宿主中立的方式描述。
5. Skill 中不得出现任何具体 Agent 宿主的名字与专属约定——那属于 Phase 2 的 Adapter 层。
