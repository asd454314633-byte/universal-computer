"""MCP provider placeholder (Phase 1: detection slot only).

If the host environment registers MCP servers, the router may prefer a native
MCP capability over Playwright. Phase 1 does not implement any MCP transport —
this module only reserves the interface and reports unavailability so the
router falls through cleanly.
"""
from __future__ import annotations

from core.protocol import ActionError, ActionResult
from ..base import BaseProvider, CapabilityInfo


class McpProvider(BaseProvider):
    name = "mcp"
    domain = "mcp"

    def __init__(self, server_registry: dict | None = None):
        # server_registry: {"server-name": {"tools": [...]}} supplied by host
        self.server_registry = server_registry or {}

    def detect(self) -> CapabilityInfo:
        return CapabilityInfo(
            self.name, self.domain, bool(self.server_registry),
            f"{len(self.server_registry)} MCP servers registered by host"
            if self.server_registry else "no MCP servers registered", [])

    def refresh_state(self) -> None:
        pass

    def dispatch(self, action: str, params: dict) -> ActionResult:
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("PROVIDER_UNAVAILABLE", "detect", False,
                                        True, "MCP transport not implemented in "
                                        "Phase 1"), False)
