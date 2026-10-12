"""Playwright browser provider — the browser primary path.

Session capabilities: fresh session, attach to running Chrome via CDP,
persistent profile dir (login state saved/restored, path never hardcoded),
multi-tab handling, download/upload, dialogs auto-dismiss, iframe access,
screenshot + accessibility snapshot.
"""
from __future__ import annotations

import os
import time
from typing import Optional

from core.protocol import (E_LOCATE_FAILED, E_PROVIDER_UNAVAILABLE, P_LOCATE,
                              ActionError, ActionResult, ProviderActionError,
                              ok, timed)
from ..base import BaseProvider, CapabilityInfo

ACTIONS = ["open", "read_text", "fill", "click", "snapshot", "screenshot",
           "list_tabs", "switch_tab", "close", "evaluate"]


class PlaywrightProvider(BaseProvider):
    name = "playwright"
    domain = "browser"

    def __init__(self, *, headless: bool = True, channel: str = "chrome",
                 profile_dir: Optional[str] = None,
                 cdp_endpoint: Optional[str] = None,
                 default_timeout_ms: int = 10000):
        self.headless = headless
        self.channel = channel
        self.profile_dir = profile_dir      # never hardcoded; caller decides
        self.cdp_endpoint = cdp_endpoint
        self.default_timeout_ms = default_timeout_ms
        self._pw = None
        self._browser = None
        self._context = None
        self._pages: list = []

    # ---- capability -------------------------------------------------------

    def detect(self) -> CapabilityInfo:
        try:
            import playwright  # noqa: F401
        except ImportError:
            return CapabilityInfo(self.name, self.domain, False,
                                  "playwright package not installed", [])
        details = f"playwright installed; channel={self.channel}"
        if self.cdp_endpoint:
            details += "; attach mode"
        if self.profile_dir:
            details += "; persistent profile"
        return CapabilityInfo(self.name, self.domain, True, details, ACTIONS)

    # ---- session ----------------------------------------------------------

    def _ensure_session(self):
        if self._context is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ProviderActionError(ActionError(
                E_PROVIDER_UNAVAILABLE, "detect", False, True, str(exc)))
        self._pw = sync_playwright().start()
        launch_kw = {"headless": self.headless, "channel": self.channel,
                     "timeout": max(self.default_timeout_ms, 30000)}
        if self.cdp_endpoint:                       # attach to running browser
            self._browser = self._pw.chromium.connect_over_cdp(
                self.cdp_endpoint, timeout=20000)
            self._context = self._browser.contexts[0] if self._browser.contexts \
                else self._browser.new_context()
        elif self.profile_dir:                      # persistent profile => saved login
            os.makedirs(self.profile_dir, exist_ok=True)
            self._context = self._pw.chromium.launch_persistent_context(
                self.profile_dir, **launch_kw)
        else:
            self._browser = self._pw.chromium.launch(**launch_kw)
            self._context = self._browser.new_context()
        self._context.set_default_timeout(self.default_timeout_ms)
        self._context.set_default_navigation_timeout(self.default_timeout_ms * 3)
        # auto-dismiss dialogs so tasks are not blocked by JS alerts
        self._context.on("page", self._bind_page)
        for p in self._context.pages:
            self._bind_page(p)

    def _bind_page(self, page):
        page.on("dialog", lambda d: d.dismiss())
        if page not in self._pages:
            self._pages.append(page)

    @property
    def page(self):
        self._ensure_session()
        if not self._pages:
            self._pages = [self._context.new_page()]
            self._bind_page(self._pages[0])
        return self._pages[-1]

    def refresh_state(self) -> None:
        """Re-acquire page state after a failed locate (recovery hook)."""
        try:
            self.page.bring_to_front()
        except Exception:
            pass

    def close(self) -> None:
        for closer in (lambda: self._context and self._context.close(),
                       lambda: self._browser and self._browser.close(),
                       lambda: self._pw and self._pw.stop()):
            try:
                closer()
            except Exception:
                pass
        self._context = self._browser = self._pw = None
        self._pages = []

    # ---- actions ----------------------------------------------------------

    def open(self, url: str, target: dict | None = None) -> ActionResult:
        target = target or {"url": url}
        def run():
            self.page.goto(url, wait_until="domcontentloaded")
            return {"url": self.page.url, "title": self.page.title()}
        return timed(self.name, "open", target, run)

    def read_text(self, selector: str, target: dict | None = None) -> ActionResult:
        target = target or {"selector": selector}
        def run():
            loc = self.page.locator(selector)
            loc.wait_for(state="attached", timeout=self.default_timeout_ms)
            return {"text": loc.inner_text()}
        return timed(self.name, "read_text", target, run)

    def fill(self, selector: str, value: str, target: dict | None = None) -> ActionResult:
        target = target or {"selector": selector, "value": value}
        def run():
            loc = self.page.locator(selector)
            loc.wait_for(state="visible", timeout=self.default_timeout_ms)
            loc.fill(value)
            return {"filled": value, "selector": selector}
        return timed(self.name, "fill", target, run)

    def click(self, selector: str, target: dict | None = None) -> ActionResult:
        target = target or {"selector": selector}
        def run():
            loc = self.page.locator(selector)
            loc.wait_for(state="visible", timeout=self.default_timeout_ms)
            loc.click()
            return {"clicked": selector}
        return timed(self.name, "click", target, run)

    def snapshot(self, target: dict | None = None) -> ActionResult:
        def run():
            return {"a11y_snapshot": self.page.accessibility.snapshot()}
        return timed(self.name, "snapshot", target or {}, run)

    def screenshot(self, path: str, target: dict | None = None) -> ActionResult:
        def run():
            self.page.screenshot(path=path)
            return {"path": path}
        return timed(self.name, "screenshot", target or {"path": path}, run)

    def list_tabs(self, target: dict | None = None) -> ActionResult:
        def run():
            return [{"url": p.url, "title": p.title()} for p in self._context.pages]
        return timed(self.name, "list_tabs", target or {}, run)

    def switch_tab(self, index: int, target: dict | None = None) -> ActionResult:
        def run():
            pages = self._context.pages
            if not 0 <= index < len(pages):
                raise LookupError(f"tab index {index} out of range")
            self._pages.append(pages[index])
            return {"switched_to": pages[index].url}
        return timed(self.name, "switch_tab", target or {"index": index}, run)

    def evaluate(self, expression: str, target: dict | None = None) -> ActionResult:
        def run():
            return {"value": self.page.evaluate(expression)}
        return timed(self.name, "evaluate", target or {"expression": expression}, run)

    # upload/download helpers used by runner
    def upload(self, selector: str, file_path: str) -> ActionResult:
        def run():
            self.page.locator(selector).set_input_files(file_path)
            return {"uploaded": file_path}
        return timed(self.name, "upload", {"selector": selector, "file": file_path}, run)

    def dispatch(self, action: str, params: dict) -> ActionResult:
        if action == "open":
            return self.open(params["url"])
        if action == "read_text":
            return self.read_text(params["selector"])
        if action == "fill":
            return self.fill(params["selector"], params["value"])
        if action == "click":
            return self.click(params["selector"])
        if action == "snapshot":
            return self.snapshot()
        if action == "screenshot":
            return self.screenshot(params["path"])
        if action == "list_tabs":
            return self.list_tabs()
        if action == "switch_tab":
            return self.switch_tab(params["index"])
        if action == "upload":
            return self.upload(params["selector"], params["file"])
        if action == "close":
            self.close()
            return ok(self.name, "close")
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("UNSUPPORTED_ACTION", "execute",
                                        False, False, f"unknown action {action}"),
                            False)
