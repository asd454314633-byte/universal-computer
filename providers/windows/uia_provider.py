"""Windows UIA provider — structured desktop automation primary path.

Uses the mature `uiautomation` library (UI Automation COM API wrapper).
Locates windows/controls by AutomationId / Name / ControlType / hierarchy —
absolute screen coordinates are never the primary locator.
"""
from __future__ import annotations

from typing import Optional

from core.protocol import (ActionError, ActionResult, ProviderActionError,
                              ok, timed)
from ..base import BaseProvider, CapabilityInfo

ACTIONS = ["list_windows", "find_window", "read_tree", "find_control",
           "invoke", "set_text", "get_value", "focus"]


class UIAProvider(BaseProvider):
    name = "uia"
    domain = "windows"

    def __init__(self, search_timeout_s: float = 5.0):
        self.search_timeout_s = search_timeout_s
        self._uia = None

    # ---- capability -------------------------------------------------------

    def detect(self) -> CapabilityInfo:
        try:
            import uiautomation as uia
        except ImportError:
            return CapabilityInfo(self.name, self.domain, False,
                                  "uiautomation package not installed", [])
        try:
            root = uia.GetRootControl()
            ok_probe = root.Name is not None
        except Exception as exc:  # noqa: BLE001
            return CapabilityInfo(self.name, self.domain, False,
                                  f"UIA root probe failed: {exc}", [])
        self._uia = uia
        return CapabilityInfo(self.name, self.domain, ok_probe,
                              "UIA root control accessible" if ok_probe
                              else "UIA root returned null", ACTIONS)

    def refresh_state(self) -> None:
        # UIA re-resolves elements on every access; nothing to pre-fetch.
        pass

    # ---- helpers ----------------------------------------------------------

    def _lib(self):
        if self._uia is None:
            import uiautomation as uia
            self._uia = uia
        return self._uia

    @staticmethod
    def _ctrl_summary(c) -> dict:
        return {
            "ControlType": c.ControlTypeName,
            "Name": c.Name,
            "AutomationId": c.AutomationId,
            "ClassName": c.ClassName,
        }

    def _resolve_window(self, name: Optional[str] = None,
                        class_name: Optional[str] = None):
        uia = self._lib()
        uia.SetGlobalSearchTimeout(self.search_timeout_s * 1000)
        kw = {"searchDepth": 1}
        if name:
            kw["Name"] = name
        if class_name:
            kw["ClassName"] = class_name
        win = uia.WindowControl(**kw)
        if not win.Exists(0, 0) and name:
            # substring fallback by walking top-level windows
            for w in uia.GetRootControl().GetChildren():
                if w.ControlTypeName == "WindowControl" and name.lower() in (w.Name or "").lower():
                    return w
            raise LookupError(f"window not found: name={name!r} class={class_name!r}")
        if not win.Exists(0, 0):
            raise LookupError(f"window not found: class={class_name!r}")
        return win

    def _resolve_control(self, window, criteria: dict):
        """IMPORTANT: search is always scoped INSIDE the given window.
        Never search from desktop root — that would match unrelated controls
        (e.g. taskbar/system tray buttons)."""
        uia = self._lib()
        ctype = (criteria.get("control_type") or "").lower()
        kw = {"searchDepth": criteria.get("search_depth", 8)}
        if criteria.get("automation_id"):
            kw["AutomationId"] = criteria["automation_id"]
        if criteria.get("name"):
            kw["Name"] = criteria["name"]
        if criteria.get("class_name"):
            kw["ClassName"] = criteria["class_name"]
        type_map = {
            "edit": "EditControl", "button": "ButtonControl", "text": "TextControl",
            "menuitem": "MenuItemControl", "menu": "MenuControl",
            "menubar": "MenuBarControl",
            "tree": "TreeControl", "treeitem": "TreeItemControl",
            "list": "ListControl", "listitem": "ListItemControl",
            "dialog": "WindowControl", "toolbar": "ToolBarControl",
            "checkbox": "CheckBoxControl", "combobox": "ComboBoxControl",
            "document": "DocumentControl", "pane": "PaneControl",
            "tabitem": "TabItemControl", "tab": "TabControl",
            "hyperlink": "HyperlinkControl", "table": "TableControl",
            "window": "WindowControl", "group": "GroupControl",
            "splitbutton": "SplitButtonControl",
        }
        if ctype:
            enum_name = type_map.get(ctype, criteria.get("control_type"))
            enum_member = getattr(uia.ControlType, enum_name, None)
            if enum_member is None:
                raise LookupError(
                    f"unknown control_type: {criteria.get('control_type')!r}")
            kw["ControlType"] = enum_member
        ctrl = window.Control(**kw)
        if not ctrl.Exists(self.search_timeout_s, 0.2):
            raise LookupError(f"control not found in window: {criteria}")
        return ctrl

    # ---- actions ----------------------------------------------------------

    def list_windows(self, target: dict | None = None) -> ActionResult:
        def run():
            uia = self._lib()
            wins = []
            for w in uia.GetRootControl().GetChildren():
                if w.ControlTypeName in ("WindowControl", "PaneControl") and w.Name:
                    wins.append(self._ctrl_summary(w))
            return {"windows": wins}
        return timed(self.name, "list_windows", target or {}, run)

    def read_tree(self, window: dict, depth: int = 4,
                  target: dict | None = None) -> ActionResult:
        def run():
            win = self._resolve_window(window.get("name"), window.get("class_name"))
            def walk(c, d):
                node = self._ctrl_summary(c)
                if d > 0:
                    node["children"] = []
                    for ch in c.GetChildren():
                        node["children"].append(walk(ch, d - 1))
                return node
            return {"tree": walk(win, depth)}
        return timed(self.name, "read_tree", target or {"window": window, "depth": depth}, run)

    def find_control(self, window: dict, criteria: dict,
                     target: dict | None = None) -> ActionResult:
        def run():
            win = self._resolve_window(window.get("name"), window.get("class_name"))
            ctrl = self._resolve_control(win, criteria)
            return {"found": self._ctrl_summary(ctrl)}
        return timed(self.name, "find_control",
                     target or {"window": window, "criteria": criteria}, run)

    def invoke(self, window: dict, criteria: dict,
               target: dict | None = None) -> ActionResult:
        def run():
            win = self._resolve_window(window.get("name"), window.get("class_name"))
            ctrl = self._resolve_control(win, criteria)
            method = None
            # 1) UIA Invoke pattern (structural, coordinate-free)
            try:
                pattern = ctrl.GetInvokePattern()
                if pattern:
                    pattern.Invoke()
                    method = "invoke-pattern"
            except Exception:
                method = None
            # 2) WM_COMMAND-free fallback: legacy default action
            if method is None:
                try:
                    ctrl.GetLegacyPattern().DoDefaultAction()
                    method = "legacy-default-action"
                except Exception:
                    method = None
            # 3) zero-interference message click for classic BUTTON controls
            if method is None and ctrl.ControlTypeName == "ButtonControl" \
                    and self._bm_click(ctrl):
                method = "bm-click"
            # 4) last structural fallback: clickable point (moves the cursor;
            #    only valid when the control is actually on top)
            if method is None:
                pt = ctrl.GetClickablePoint()
                if pt is None:
                    raise LookupError("control has no invoke/default action "
                                      "and no clickable point")
                self._lib().Click(pt[0], pt[1])
                method = "clickable-point"
            return {"invoked": self._ctrl_summary(ctrl), "method": method}
        return timed(self.name, "invoke",
                     target or {"window": window, "criteria": criteria}, run)

    # ---- classic-win32 helpers (structural: hwnd-based, no coordinates) ----

    @staticmethod
    def _hwnd_of(ctrl) -> int:
        return ctrl.NativeWindowHandle or 0

    def _wm_set_text(self, ctrl, value: str) -> bool:
        import ctypes
        hwnd = self._hwnd_of(ctrl)
        if not hwnd:
            return False
        WM_SETTEXT = 0x000C
        res = ctypes.windll.user32.SendMessageTimeoutW(
            hwnd, WM_SETTEXT, 0, value, 0x0002, 2000,
            ctypes.byref(ctypes.c_size_t()))
        return bool(res)

    def _wm_get_text(self, ctrl) -> str:
        import ctypes
        hwnd = self._hwnd_of(ctrl)
        if not hwnd:
            return ""
        WM_GETTEXTLENGTH, WM_GETTEXT = 0x000E, 0x000D
        size = ctypes.windll.user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
        if size <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(size + 1)
        ctypes.windll.user32.SendMessageW(hwnd, WM_GETTEXT, size + 1, buf)
        return buf.value

    def _bm_click(self, ctrl) -> bool:
        """Send BM_CLICK to a classic button hwnd — no mouse movement,
        works for background windows."""
        import ctypes
        hwnd = self._hwnd_of(ctrl)
        if not hwnd:
            return False
        BM_CLICK = 0x00F5
        res = ctypes.windll.user32.SendMessageTimeoutW(
            hwnd, BM_CLICK, 0, 0, 0x0002, 2000,
            ctypes.byref(ctypes.c_size_t()))
        return bool(res)

    def set_text(self, window: dict, criteria: dict, value: str,
                 target: dict | None = None) -> ActionResult:
        def run():
            win = self._resolve_window(window.get("name"), window.get("class_name"))
            ctrl = self._resolve_control(win, criteria)
            method = None
            # 1) UIA ValuePattern (void return — success is "no exception")
            try:
                pattern = ctrl.GetValuePattern()
                if pattern:
                    pattern.SetValue(value)
                    method = "value-pattern"
            except Exception:
                method = None
            # 2) WM_SETTEXT to the control's hwnd (structural, not coordinate)
            if method is None and self._wm_set_text(ctrl, value):
                method = "wm-settext"
            # 3) keyboard fallback into the focused control
            if method is None:
                ctrl.SetFocus()
                ctrl.SendKeys("{Ctrl}a{Del}")
                ctrl.SendKeys(value, waitTime=0.05)
                method = "sendkeys"
            return {"set": self._ctrl_summary(ctrl), "method": method,
                    "value": value}
        return timed(self.name, "set_text",
                     target or {"window": window, "criteria": criteria}, run)

    def get_value(self, window: dict, criteria: dict,
                  target: dict | None = None) -> ActionResult:
        def run():
            win = self._resolve_window(window.get("name"), window.get("class_name"))
            ctrl = self._resolve_control(win, criteria)
            # 1) UIA ValuePattern.Value
            val = None
            try:
                pattern = ctrl.GetValuePattern()
                if pattern:
                    val = pattern.Value
            except Exception:
                val = None
            # 2) WM_GETTEXT
            if val is None or val == "":
                wm = self._wm_get_text(ctrl)
                if wm:
                    val = wm
            # 3) Name as last resort
            if val is None or val == "":
                val = ctrl.Name
            return {"value": val, "control": self._ctrl_summary(ctrl)}
        return timed(self.name, "get_value",
                     target or {"window": window, "criteria": criteria}, run)

    def focus(self, window: dict, target: dict | None = None) -> ActionResult:
        def run():
            win = self._resolve_window(window.get("name"), window.get("class_name"))
            win.SetActive()
            return {"focused": self._ctrl_summary(win)}
        return timed(self.name, "focus", target or {"window": window}, run)

    def dispatch(self, action: str, params: dict) -> ActionResult:
        if action == "list_windows":
            return self.list_windows()
        if action == "read_tree":
            return self.read_tree(params["window"], params.get("depth", 4))
        if action == "find_control":
            return self.find_control(params["window"], params["criteria"])
        if action == "invoke":
            return self.invoke(params["window"], params["criteria"])
        if action == "set_text":
            return self.set_text(params["window"], params["criteria"],
                                 params["value"])
        if action == "get_value":
            return self.get_value(params["window"], params["criteria"])
        if action == "focus":
            return self.focus(params["window"])
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("UNSUPPORTED_ACTION", "execute",
                                        False, False, f"unknown action {action}"),
                            False)
