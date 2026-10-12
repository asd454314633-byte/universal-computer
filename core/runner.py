"""Task runner: executes a declarative task through the CapabilityRouter,
records state, audits every action, and applies the recovery policy.

Task JSON format:
{
  "task_id": "example-task",
  "domain": "browser" | "windows" | "auto",
  "steps": [
    {"step_id": "s1", "action": "open", "params": {"url": "..."},
     "risk": "READ" | "WRITE" | "DESTRUCTIVE" (optional override),
     "provider": "playwright" (optional pin)}
  ]
}
"""
from __future__ import annotations

import json
import time
import uuid

from .audit import AuditLogger
from .protocol import (ActionError, ActionResult, E_PERMISSION_DENIED,
                       E_PROVIDER_UNAVAILABLE, E_RUNTIME_ERROR)
from .recovery import run_with_recovery
from .router import CapabilityRouter
from .security import RiskLevel, classify
from .state import FAILED, RUNNING, StepRecord, SUCCESS, StateStore, TaskRecord


class TaskRunner:
    def __init__(self, router: CapabilityRouter, *,
                 state_dir: str = "logs/state",
                 audit_dir: str = "evidence/audit",
                 confirm_callback=None):
        self.router = router
        self.store = StateStore(state_dir)
        self.audit = AuditLogger(audit_dir)
        # host injects confirmation for WRITE/DESTRUCTIVE; core never prompts
        self.confirm_callback = confirm_callback

    def _provider_for(self, task: TaskRecord, step: dict):
        domain = task.domain
        pinned = step.get("provider")
        if pinned:
            if pinned not in self.router.providers:
                raise RuntimeError(f"pinned provider not registered: {pinned}")
            return self.router.providers[pinned], f"pinned by task: {pinned}"
        decision = self.router.route(
            domain, use_com=bool(step.get("use_com", False)))
        if decision.provider == "none":
            raise RuntimeError(decision.reason)
        return self.router.providers[decision.provider], decision.reason

    def run(self, task_def: dict) -> dict:
        task = TaskRecord(
            task_id=task_def.get("task_id") or f"task-{uuid.uuid4().hex[:8]}",
            session_id=task_def.get("session_id") or uuid.uuid4().hex[:12],
            domain=task_def.get("domain", "auto"),
        )
        task.status = RUNNING
        self.store.save(task)

        records = []
        fatal = False
        for i, step in enumerate(task_def.get("steps", []), start=1):
            if fatal:
                rec = StepRecord(step.get("step_id", f"s{i}"), "-", step.get("action", "?"),
                                 status="CANCELLED")
                records.append(rec)
                continue
            rec = self._run_step(task, step, i)
            task.steps.append(rec)
            records.append(rec)
            self.store.save(task)
            if rec.status != SUCCESS:
                fatal = True

        if all(r.status == SUCCESS for r in records) and records:
            task.status = SUCCESS
        elif any(r.status == FAILED for r in records):
            task.status = FAILED
        elif any(r.status == "CANCELLED" for r in records):
            task.status = "CANCELLED"
        self.store.save(task)
        return {
            "task": {
                "task_id": task.task_id,
                "session_id": task.session_id,
                "status": task.status,
                "completed_steps": task.completed_step_ids(),
                "failed_steps": task.failed_step_ids(),
                "resumable": task.resumable(),
                "needs_session_reinit": task.needs_session_reinit(),
            },
            "steps": [
                {"step_id": r.step_id, "provider": r.provider, "action": r.action,
                 "status": r.status, "duration_ms": r.duration_ms,
                 "error": r.error, "evidence": r.evidence}
                for r in records
            ],
        }

    def _run_step(self, task: TaskRecord, step: dict, index: int) -> StepRecord:
        step_id = step.get("step_id", f"s{index}")
        action = step["action"]
        params = step.get("params", {})
        risk = classify(action, step.get("risk"))

        rec = StepRecord(step_id, "-", action, params, status=RUNNING,
                         started_at=time.time())
        try:
            provider, reason = self._provider_for(task, step)
        except Exception as exc:  # noqa: BLE001
            rec.status = FAILED
            rec.finished_at = time.time()
            rec.error = ActionError(E_PROVIDER_UNAVAILABLE, "detect", True, True,
                                    str(exc)).to_dict()
            return rec
        rec.provider = provider.name

        # risk gate: core only declares; host decides confirmation
        if risk.level in (RiskLevel.WRITE, RiskLevel.DESTRUCTIVE) \
                and self.confirm_callback is not None:
            if not self.confirm_callback(task.task_id, step_id, risk):
                rec.status = FAILED
                rec.finished_at = time.time()
                rec.error = ActionError(E_PERMISSION_DENIED, "detect", False,
                                        False,
                                        f"host refused {risk.level} action "
                                        f"{action}").to_dict()
                return rec

        def attempt(is_retry: bool) -> ActionResult:
            if is_retry:
                params2 = dict(params)
                params2["recovery_hint"] = "re-locate after state refresh"
            else:
                params2 = params
            try:
                return provider.dispatch(action, params2)
            except LookupError:
                raise
            except Exception as exc:  # noqa: BLE001
                return ActionResult(False, provider.name, action, params2,
                                    None, [], 0,
                                    ActionError(E_RUNTIME_ERROR, "execute",
                                                True, True, str(exc)), False)

        result = run_with_recovery(provider, action, params, attempt)

        rec.duration_ms = result.duration_ms
        rec.finished_at = time.time()
        rec.evidence = result.evidence
        if result.success:
            rec.status = SUCCESS
        else:
            rec.status = FAILED
            rec.error = result.error.to_dict() if result.error else \
                {"type": E_RUNTIME_ERROR, "phase": "execute"}

        self.audit.log(task_id=task.task_id, step_id=step_id,
                       provider=provider.name, action=action, target=params,
                       success=result.success, duration_ms=result.duration_ms,
                       fallback_reason=reason,
                       error=rec.error, evidence=result.evidence)
        return rec


def load_task(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
