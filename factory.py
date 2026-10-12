"""Provider factory: assemble the default provider set + router + runner.

This is the single composition root. Agent hosts (adapters, Phase 2) only
ever call these factories — never instantiate internals themselves.
"""
from __future__ import annotations

import os

from core.router import CapabilityRouter
from core.runner import TaskRunner
from providers.browser.playwright_provider import PlaywrightProvider
from providers.mcp.mcp_provider import McpProvider
from providers.visual.visual_provider import MockVisualProvider
from providers.webmcp.webmcp_provider import WebMcpProvider
from providers.windows.com_provider import ComProvider
from providers.windows.uia_provider import UIAProvider
from providers.windows.win32_provider import Win32Provider


def build_router(*, webmcp_enabled: bool = False,
                 visual_enabled: bool = False,
                 browser_headless: bool = True,
                 browser_channel: str = "chrome",
                 browser_profile_dir: str | None = None,
                 browser_cdp_endpoint: str | None = None,
                 mcp_servers: dict | None = None) -> tuple[CapabilityRouter, dict]:
    """Returns (router, providers-by-name)."""
    pw = PlaywrightProvider(headless=browser_headless, channel=browser_channel,
                            profile_dir=browser_profile_dir,
                            cdp_endpoint=browser_cdp_endpoint)
    providers = {
        "playwright": pw,
        "webmcp": WebMcpProvider(pw, enabled=webmcp_enabled),
        "uia": UIAProvider(),
        "win32": Win32Provider(),
        "com": ComProvider(),
        "visual": MockVisualProvider(),
        "mcp": McpProvider(mcp_servers),
    }
    router = CapabilityRouter(list(providers.values()),
                              webmcp_enabled=webmcp_enabled,
                              visual_enabled=visual_enabled)
    return router, providers


def build_runner(router: CapabilityRouter, *, base_dir: str | None = None,
                 confirm_callback=None) -> TaskRunner:
    base = base_dir or os.getcwd()
    return TaskRunner(router,
                      state_dir=os.path.join(base, "logs", "state"),
                      audit_dir=os.path.join(base, "evidence", "audit"),
                      confirm_callback=confirm_callback)
