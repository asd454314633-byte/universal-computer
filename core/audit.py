"""Audit log: one JSONL line per real action.

Fields: time, task_id, step_id, provider, action, target, outcome, duration_ms,
fallback_reason, evidence paths. Evidence is kept for failures and for the
final result of each step — never unbounded screenshot dumps.
"""
from __future__ import annotations

import json
import os
import time
from typing import Optional


class AuditLogger:
    def __init__(self, base_dir: str):
        self.base = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _file(self) -> str:
        return os.path.join(self.base, f"{time.strftime('%Y-%m-%d')}.jsonl")

    def log(self, *, task_id: str, step_id: str, provider: str, action: str,
            target: dict, success: bool, duration_ms: int,
            fallback_reason: Optional[str] = None,
            error: Optional[dict] = None,
            evidence: Optional[list] = None) -> dict:
        rec = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "task_id": task_id,
            "step_id": step_id,
            "provider": provider,
            "action": action,
            "target": target,
            "outcome": "SUCCESS" if success else "FAILED",
            "duration_ms": duration_ms,
            "fallback_reason": fallback_reason,
            "error": error,
            "evidence": (evidence or [])[:8],   # cap: keep key evidence only
        }
        with open(self._file(), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        return rec
