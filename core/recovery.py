"""Recovery policy: on locate failure, refresh state, re-locate, then either
succeed or return a definitive structured failure. Hard attempt cap — infinite
retry loops are forbidden.
"""
from __future__ import annotations

from typing import Callable

from .protocol import (ActionError, ActionResult, E_LOCATE_FAILED, P_LOCATE,
                       ProviderActionError, fail, ok)


def run_with_recovery(provider, action: str, target: dict,
                      attempt_fn: Callable[[bool], ActionResult],
                      max_attempts: int = 2) -> ActionResult:
    """attempt_fn(is_retry: bool) -> ActionResult.

    Attempt 1 runs normally. If it fails with LOCATE_FAILED, the provider
    refreshes its page/window state, then a single re-locate attempt is made.
    Total attempts <= max_attempts (default 2). No polling loops.
    """
    last: ActionResult | None = None
    for attempt in range(max_attempts):
        is_retry = attempt > 0
        if is_retry:
            try:
                provider.refresh_state()
            except Exception:
                pass  # refresh is best-effort; the retry itself is the test
        res = attempt_fn(is_retry)
        if res.success:
            res.recovered = is_retry
            return res
        last = res
        if (res.error is None
                or res.error.type != E_LOCATE_FAILED
                or not res.error.retryable):
            return res  # definitive failure — do not loop
    # exhausted: return the last structured failure untouched
    return last
