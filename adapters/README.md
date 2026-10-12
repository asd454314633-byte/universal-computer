# Adapters（Phase 2 预留，本阶段仅接口说明）

Phase 1 不建立任何宿主正式 Adapter。Phase 2 (`PHASE2_AGENT_ADAPTERS`) 将依次制作：

- WorkBuddy Adapter
- Codex Adapter
- Qoder CN Adapter

三者的唯一职责：把宿主的"能力/工具调用协议"翻译成对本 Core 的进程调用或
factory API 调用，并把 Core 的 JSON 结果翻译回宿主格式。

硬性规则：

1. 三者必须调用**同一个** Universal Core，禁止复制或修改 Core 形成分叉。
2. 确认 UI、会话偏好、宿主专属配置只存在于 Adapter 层。
3. 未来新增宿主 = 只新增 Adapter。
