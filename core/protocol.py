"""Universal Computer Core — unified result protocol.

Every provider action MUST return an ActionResult. Failures must carry a
structured ActionError (type / phase / retryable / degrade_allowed / raw),
never a bare "failed".
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional


# ---- Error taxonomy -------------------------------------------------------

# Error types (stable strings, safe for callers to switch on)
E_PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"   # provider not installed/launchable
E_LOCATE_FAILED = "LOCATE_FAILED"                 # target element/window not found
E_TIMEOUT = "TIMEOUT"
E_PERMISSION_DENIED = "PERMISSION_DENIED"         # risk gate refused the action
E_RUNTIME_ERROR = "RUNTIME_ERROR"
E_UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
E_RECOVERED = "RECOVERED"                         # recovered via retry/refetch

# Phases
P_DETECT = "detect"
P_LOCATE = "locate"
P_EXECUTE = "execute"
P_VERIFY = "verify"


@dataclass
class ActionError:
    type: str
    phase: str
    retryable: bool
    degrade_allowed: bool
    raw: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "phase": self.phase,
            "retryable": self.retryable,
            "degrade_allowed": self.degrade_allowed,
            "raw": self.raw[:2000],
        }

    @staticmethod
    def from_exception(exc: BaseException, phase: str = P_EXECUTE) -> "ActionError":
        mapping = {
            TimeoutError: (E_TIMEOUT, True, True),
            LookupError: (E_LOCATE_FAILED, True, True),
        }
        etype, retryable, degrade = mapping.get(
            type(exc), (E_RUNTIME_ERROR, True, True)
        )
        return ActionError(
            type=etype,
            phase=phase,
            retryable=retryable,
            degrade_allowed=degrade,
            raw="".join(traceback.format_exception_only(type(exc), exc)).strip(),
        )


@dataclass
class ActionResult:
    success: bool
    provider: str
    action: str
    target: dict = field(default_factory=dict)
    result: Any = None
    evidence: list = field(default_factory=list)   # evidence file paths / inline refs
    duration_ms: int = 0
    error: Optional[ActionError] = None
    recovered: bool = False                         # True if a retry/refetch rescued it

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "provider": self.provider,
            "action": self.action,
            "target": self.target,
            "result": self.result,
            "evidence": self.evidence,
            "duration_ms": self.duration_ms,
            "error": self.error.to_dict() if self.error else None,
            "recovered": self.recovered,
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


def ok(provider: str, action: str, result: Any = None, target: dict | None = None,
       evidence: list | None = None, duration_ms: int = 0,
       recovered: bool = False) -> ActionResult:
    return ActionResult(True, provider, action, target or {}, result,
                        evidence or [], duration_ms, None, recovered)


def fail(provider: str, action: str, error: ActionError, target: dict | None = None,
         result: Any = None, evidence: list | None = None) -> ActionResult:
    return ActionResult(False, provider, action, target or {}, result,
                        evidence or [], 0, error, False)


def timed(provider: str, action: str, target: dict, fn, **kwargs) -> ActionResult:
    """Run fn() and wrap its return/exception into an ActionResult."""
    t0 = time.monotonic()
    try:
        result = fn(**kwargs)
    except Exception as exc:  # noqa: BLE001 - boundary must not raise
        if isinstance(exc, ProviderActionError):
            return ActionResult(False, provider, action, target, None, [],
                                int((time.monotonic() - t0) * 1000), exc.error, False)
        return ActionResult(False, provider, action, target, None, [],
                            int((time.monotonic() - t0) * 1000),
                            ActionError.from_exception(exc), False)
    dur = int((time.monotonic() - t0) * 1000)
    if isinstance(result, ActionResult):
        result.duration_ms = dur
        result.recovered = result.recovered or False
        return result
    return ok(provider, action, result, target, duration_ms=dur)


class ProviderActionError(Exception):
    """Providers raise this to signal a classified failure."""

    def __init__(self, error: ActionError):
        super().__init__(error.raw or error.type)
        self.error = error
