"""Task/step state machine with persisted session state.

States: PENDING -> RUNNING -> SUCCESS | FAILED | CANCELLED
On failure the record answers: which step failed, what completed, whether the
task can continue, whether a session re-init is required.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Optional

PENDING = "PENDING"
RUNNING = "RUNNING"
SUCCESS = "SUCCESS"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
VALID = {PENDING, RUNNING, SUCCESS, FAILED, CANCELLED}


@dataclass
class StepRecord:
    step_id: str
    provider: str
    action: str
    target: dict = field(default_factory=dict)
    status: str = PENDING
    started_at: float = 0.0
    finished_at: float = 0.0
    duration_ms: int = 0
    error: Optional[dict] = None
    evidence: list = field(default_factory=list)


@dataclass
class TaskRecord:
    task_id: str
    session_id: str
    domain: str            # browser | windows | auto
    status: str = PENDING
    steps: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    note: str = ""

    def failed_step_ids(self) -> list:
        return [s.step_id for s in self.steps if s.status == FAILED]

    def completed_step_ids(self) -> list:
        return [s.step_id for s in self.steps if s.status == SUCCESS]

    def resumable(self) -> bool:
        """A failed task is resumable if at least one step failed but the
        failed step is not the very first structural init step."""
        return self.status == FAILED and len(self.completed_step_ids()) >= 1

    def needs_session_reinit(self) -> bool:
        for s in self.steps:
            if s.status == FAILED and (s.error or {}).get("type") == "SESSION_LOST":
                return True
        return False


class StateStore:
    """Persists one JSON file per task under <base>/<task_id>.json."""

    def __init__(self, base_dir: str):
        self.base = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, task_id: str) -> str:
        safe = "".join(c for c in task_id if c.isalnum() or c in "-_")
        return os.path.join(self.base, f"{safe}.json")

    def save(self, task: TaskRecord) -> None:
        task.updated_at = time.time()
        with open(self._path(task.task_id), "w", encoding="utf-8") as f:
            json.dump(asdict(task), f, ensure_ascii=False, indent=2, default=str)

    def load(self, task_id: str) -> Optional[TaskRecord]:
        p = self._path(task_id)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        steps = [StepRecord(**s) for s in data.pop("steps", [])]
        t = TaskRecord(**data)
        t.steps = steps
        return t
