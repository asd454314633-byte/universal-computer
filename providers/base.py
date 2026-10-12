"""Provider base contract. Every provider implements detect() and a set of
declared actions; every action returns ActionResult."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CapabilityInfo:
    provider: str
    domain: str                    # browser | windows | visual | mcp
    available: bool
    details: str = ""
    actions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "domain": self.domain,
            "available": self.available,
            "details": self.details,
            "actions": self.actions,
        }


class BaseProvider(ABC):
    name: str = "base"
    domain: str = "browser"

    @abstractmethod
    def detect(self) -> CapabilityInfo:
        """Probe whether this provider can actually run right now.
        Must be cheap and side-effect free (no window grabs, no launches)."""

    @abstractmethod
    def refresh_state(self) -> None:
        """Best-effort state re-acquisition used by the recovery policy."""

    def close(self) -> None:
        """Release provider-owned resources (browser session etc.)."""
