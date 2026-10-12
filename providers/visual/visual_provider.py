"""VisualProvider — pluggable visual fallback interface (Phase 1: interface
+ mock only; no visual model is bound to the core).

Implementations may later wrap Fara / UI-TARS / OpenAI / Gemini computer-use
models. The core never knows which model sits behind this interface.
"""
from __future__ import annotations

from typing import Any, Optional

from core.protocol import (ActionError, ActionResult, timed)
from ..base import BaseProvider, CapabilityInfo

ACTIONS = ["observe", "locate", "click", "type", "drag", "scroll", "verify"]


class VisualProvider(BaseProvider):
    name = "visual"
    domain = "visual"

    def detect(self) -> CapabilityInfo:
        return CapabilityInfo(self.name, self.domain, False,
                              "no visual backend registered (mock only)", ACTIONS)

    def refresh_state(self) -> None:
        pass

    # ---- standard interface (contract, not implementation) ----------------

    def observe(self) -> dict:
        raise NotImplementedError

    def locate(self, description: str) -> dict:
        raise NotImplementedError

    def click(self, target: dict) -> ActionResult:
        raise NotImplementedError

    def type(self, text: str) -> ActionResult:
        raise NotImplementedError

    def drag(self, src: dict, dst: dict) -> ActionResult:
        raise NotImplementedError

    def scroll(self, amount: int) -> ActionResult:
        raise NotImplementedError

    def verify(self, expectation: str) -> ActionResult:
        raise NotImplementedError

    def dispatch(self, action: str, params: dict) -> ActionResult:
        return ActionResult(False, self.name, action, params, None, [], 0,
                            ActionError("PROVIDER_UNAVAILABLE", "detect", False,
                                        False, "no visual backend registered"),
                            False)


class MockVisualProvider(VisualProvider):
    """Deterministic mock for interface tests. Never clicks anything.

    Keeps the logical provider name `visual` so the router ladder can address
    whichever backend is registered under this slot."""

    name = "visual"

    def detect(self) -> CapabilityInfo:
        return CapabilityInfo(self.name, self.domain, True,
                              "mock backend (no real screen interaction)",
                              ACTIONS)

    def observe(self) -> dict:
        return {"mock": True, "elements": []}

    def locate(self, description: str) -> dict:
        return {"mock": True, "description": description, "found": False}

    def click(self, target: dict) -> ActionResult:
        return ActionResult(False, self.name, "click", target, None, [], 0,
                            ActionError("PROVIDER_UNAVAILABLE", "execute", True,
                                        False, "mock provider cannot click"),
                            False)
