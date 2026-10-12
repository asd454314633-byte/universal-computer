"""COM provider — interface + detection only in Phase 1.

When a desktop application exposes a stable COM interface (Office, Excel,
Outlook, ...), it must be preferred over any UI operation. This provider
declares the contract and performs non-intrusive detection via the registry
(ProgID existence). Real COM operations are dispatched by the same action
protocol once an app adapter is needed.
"""
from __future__ import annotations

from core.protocol import (ActionError, ActionResult, timed)
from ..base import BaseProvider, CapabilityInfo

ACTIONS = ["detect_progid", "dispatch_com"]


def _progid_exists(progid: str) -> bool:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid):
            return True
    except OSError:
        return False


class ComProvider(BaseProvider):
    name = "com"
    domain = "windows"

    def detect(self) -> CapabilityInfo:
        try:
            import win32com.client  # noqa: F401
        except ImportError:
            return CapabilityInfo(self.name, self.domain, False,
                                  "pywin32 (win32com) not installed", ACTIONS)
        return CapabilityInfo(self.name, self.domain, True,
                              "win32com available; per-app ProgID detected at "
                              "task time via registry", ACTIONS)

    def refresh_state(self) -> None:
        pass

    def detect_progid(self, progid: str) -> ActionResult:
        def run():
            return {"progid": progid, "registered": _progid_exists(progid)}
        return timed(self.name, "detect_progid", {"progid": progid}, run)

    def dispatch_com(self, progid: str, statement: str) -> ActionResult:
        """Run a late-bound COM call, e.g. statement as a callable receiving
        the app object. Kept minimal: real usage belongs to per-app adapters."""
        def run():
            import win32com.client
            if not _progid_exists(progid):
                raise LookupError(f"ProgID not registered: {progid}")
            app = win32com.client.Dispatch(progid)
            return {"result": statement(app) if callable(statement) else None}
        return timed(self.name, "dispatch_com", {"progid": progid}, run)

    def dispatch(self, action: str, params: dict) -> ActionResult:
        if action == "detect_progid":
            return self.detect_progid(params["progid"])
        if action == "dispatch_com":
            return self.dispatch_com(params["progid"], params.get("statement"))
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("UNSUPPORTED_ACTION", "execute", False,
                                        False, f"unknown action {action}"), False)
