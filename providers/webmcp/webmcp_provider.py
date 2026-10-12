"""WebMCP detector — experimental capability, opt-in only.

Default OFF. When enabled, the router checks whether a page exposes the
experimental WebMCP surface before falling through to Playwright. WebMCP is
never a required dependency: unavailability must never fail a task.
"""
from __future__ import annotations

from core.protocol import ActionError, ActionResult
from ..base import BaseProvider, CapabilityInfo

DETECT_SCRIPT = """
() => {
  const c = window.navigator;
  return !!(c && (c.webmcp || window.webmcp || c.modelContext));
}
"""


class WebMcpProvider(BaseProvider):
    name = "webmcp"
    domain = "browser"

    def __init__(self, playwright_provider=None, enabled: bool = False):
        self.pw = playwright_provider
        self.enabled = enabled

    def detect(self) -> CapabilityInfo:
        if not self.enabled:
            return CapabilityInfo(self.name, self.domain, False,
                                  "opt-in disabled (default)", ["detect_site"])
        return CapabilityInfo(self.name, self.domain, True,
                              "opt-in enabled; per-site probe at task time",
                              ["detect_site"])

    def refresh_state(self) -> None:
        pass

    def detect_site(self, url: str) -> ActionResult:
        """Probe one page for a WebMCP surface. Requires the playwright
        provider for the actual check; result is advisory only."""
        if not self.pw:
            return ActionResult(False, self.name, "detect_site", {"url": url},
                                None, [], 0,
                                ActionError("PROVIDER_UNAVAILABLE", "detect",
                                            False, True, "no browser session"),
                                False)
        try:
            res = self.pw.evaluate(DETECT_SCRIPT)
            return ActionResult(True, self.name, "detect_site", {"url": url},
                                {"webmcp_available": bool(res.result["value"])},
                                [], 0, None, False)
        except Exception as exc:  # noqa: BLE001
            return ActionResult(False, self.name, "detect_site", {"url": url},
                                None, [], 0, ActionError(
                                    "RUNTIME_ERROR", "execute", True, True,
                                    str(exc)), False)

    def dispatch(self, action: str, params: dict) -> ActionResult:
        if action == "detect_site":
            return self.detect_site(params["url"])
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("UNSUPPORTED_ACTION", "execute", False,
                                        False, "WebMCP is probe-only in Phase 1"),
                            False)
