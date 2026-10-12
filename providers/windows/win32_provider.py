"""Win32 window-layer provider (window find / focus / state via pywin32 or
ctypes). Sits below UIA in the ladder: it can manage windows but cannot read
structured control trees."""
from __future__ import annotations

from core.protocol import (ActionError, ActionResult, timed)
from ..base import BaseProvider, CapabilityInfo

ACTIONS = ["list_windows", "focus", "get_foreground", "get_window_rect"]


class Win32Provider(BaseProvider):
    name = "win32"
    domain = "windows"

    def detect(self) -> CapabilityInfo:
        try:
            import win32gui  # noqa: F401
            backend = "pywin32"
        except ImportError:
            try:
                import ctypes  # noqa: F401
                backend = "ctypes"
            except ImportError:
                return CapabilityInfo(self.name, self.domain, False,
                                      "no win32 backend", [])
        return CapabilityInfo(self.name, self.domain, True,
                              f"backend={backend}", ACTIONS)

    def refresh_state(self) -> None:
        pass

    @staticmethod
    def _enum_windows() -> list:
        import win32gui
        out = []
        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    out.append({
                        "hwnd": hwnd,
                        "title": title,
                        "class_name": win32gui.GetClassName(hwnd),
                    })
        win32gui.EnumWindows(cb, None)
        return out

    def list_windows(self, target: dict | None = None) -> ActionResult:
        try:
            wins = self._enum_windows()
        except ImportError:
            return ActionResult(False, self.name, "list_windows", {}, None, [],
                                0, ActionError("PROVIDER_UNAVAILABLE", "detect",
                                               False, True, "pywin32 missing"), False)
        return timed(self.name, "list_windows", target or {}, lambda: {"windows": wins})

    def focus(self, title_substr: str, target: dict | None = None) -> ActionResult:
        def run():
            import win32gui
            matches = [w for w in self._enum_windows()
                       if title_substr.lower() in w["title"].lower()]
            if not matches:
                raise LookupError(f"no window matching {title_substr!r}")
            win32gui.SetForegroundWindow(matches[0]["hwnd"])
            return {"focused": matches[0]}
        return timed(self.name, "focus", target or {"title": title_substr}, run)

    def get_foreground(self, target: dict | None = None) -> ActionResult:
        def run():
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            return {"hwnd": hwnd, "title": win32gui.GetWindowText(hwnd),
                    "class_name": win32gui.GetClassName(hwnd)}
        return timed(self.name, "get_foreground", target or {}, run)

    def dispatch(self, action: str, params: dict) -> ActionResult:
        if action == "list_windows":
            return self.list_windows()
        if action == "focus":
            return self.focus(params["title"])
        if action == "get_foreground":
            return self.get_foreground()
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("UNSUPPORTED_ACTION", "execute", False,
                                        False, f"unknown action {action}"), False)
