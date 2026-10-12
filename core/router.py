"""Capability Router: detect first, then route. Providers are only attempted
in a fixed structural-first ladder; blind polling across all providers is
forbidden.

Browser ladder : (webmcp, opt-in) -> playwright -> visual
Windows ladder : com (when app COM hint present) -> uia -> win32 -> visual
"""
from __future__ import annotations

from dataclasses import dataclass, field

from providers.base import BaseProvider, CapabilityInfo


@dataclass
class RouteDecision:
    domain: str
    provider: str
    reason: str
    ladder: list = field(default_factory=list)   # ordered candidate names


class CapabilityRouter:
    def __init__(self, providers: list[BaseProvider], *,
                 webmcp_enabled: bool = False,
                 visual_enabled: bool = False):
        self.providers = {p.name: p for p in providers}
        self.webmcp_enabled = webmcp_enabled
        self.visual_enabled = visual_enabled
        self._detect_cache: dict[str, CapabilityInfo] = {}

    # ---- detection --------------------------------------------------------

    def detect_all(self, force: bool = False) -> dict:
        out = {}
        for name, p in self.providers.items():
            if force or name not in self._detect_cache:
                try:
                    self._detect_cache[name] = p.detect()
                except Exception as exc:  # noqa: BLE001
                    self._detect_cache[name] = CapabilityInfo(
                        name, p.domain, False, f"detect error: {exc}", [])
            out[name] = self._detect_cache[name].to_dict()
        return out

    def _available(self, name: str) -> bool:
        if name not in self.providers:
            return False
        if name not in self._detect_cache:
            self.detect_all()
        return self._detect_cache[name].available

    # ---- routing ----------------------------------------------------------

    def route(self, domain: str, *, use_com: bool = False) -> RouteDecision:
        if domain == "browser":
            ladder = []
            if self.webmcp_enabled:
                ladder.append("webmcp")
            ladder += ["playwright", "visual"]
            for name in ladder:
                if name == "webmcp" and not self.webmcp_enabled:
                    continue
                if name == "visual" and not self.visual_enabled:
                    continue
                if self._available(name):
                    reason = {
                        "webmcp": "site exposes WebMCP and opt-in flag enabled",
                        "playwright": "structural DOM automation available (primary path)",
                        "visual": "fallback: no structural provider available",
                    }[name]
                    return RouteDecision(domain, name, reason, ladder)
            return RouteDecision(domain, "none",
                                 "no available provider in browser ladder", ladder)

        if domain == "windows":
            ladder = (["com"] if use_com else []) + ["uia", "win32", "visual"]
            for name in ladder:
                if name == "visual" and not self.visual_enabled:
                    continue
                if name == "com" and not use_com:
                    continue
                if self._available(name):
                    reason = {
                        "com": "app exposes stable COM interface and task hint requested it",
                        "uia": "UIA control tree available (primary structured path)",
                        "win32": "window-level Win32 operations available",
                        "visual": "fallback: no structural provider available",
                    }[name]
                    return RouteDecision(domain, name, reason, ladder)
            return RouteDecision(domain, "none",
                                 "no available provider in windows ladder", ladder)

        raise ValueError(f"unknown domain: {domain}")
