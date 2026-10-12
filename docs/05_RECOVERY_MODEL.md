# 05_RECOVERY_MODEL.md — 状态与恢复

## 状态机

```
PENDING → RUNNING → SUCCESS | FAILED | CANCELLED
```

每个任务持久化到 `logs/state/<task_id>.json`（TaskRecord + StepRecord 列表）。

## 失败后必须可回答

- 哪一步失败：`failed_steps`
- 已完成什么：`completed_steps`
- 能否继续：`resumable`（至少完成一步才可续跑）
- 是否需重建会话：`needs_session_reinit`（存在 SESSION_LOST 类错误时）

## 恢复策略（core/recovery.py）

```
attempt 1（正常执行）
  └─ LOCATE_FAILED 且 retryable？
       └─ provider.refresh_state()（重获取页面/窗口状态）
            └─ attempt 2（重定位）
                 └─ 成功 → 返回结果并标记 recovered=true
                 └─ 失败 → 返回最终结构化失败
```

- 硬性尝试上限 `max_attempts=2`，禁止无限循环（F1 验证）。
- 非 LOCATE_FAILED 的失败是确定性失败，立即返回，不重试。
- 整条任务不会因单步失败从头重跑：后续步骤标记 CANCELLED，
  已完成步骤保留在状态文件中。
