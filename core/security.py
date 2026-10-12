"""Security model: action risk declaration only.

The core DECLARES the risk level of every action. Whether/how to confirm is
the responsibility of the calling host (agent). No host-specific confirmation
UI or policy is allowed inside the core.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    READ = "READ"                    # browse / read text / screenshot / inspect
    WRITE = "WRITE"                  # type text, fill forms, upload, save files
    DESTRUCTIVE = "DESTRUCTIVE"      # delete, overwrite, pay, irreversible submit,
                                     # modify system, send external messages


# action name -> risk level. Providers must register their actions here.
RISK_MAP: dict[str, RiskLevel] = {
    # browser
    "open": RiskLevel.READ,
    "read_text": RiskLevel.READ,
    "snapshot": RiskLevel.READ,
    "screenshot": RiskLevel.READ,
    "list_tabs": RiskLevel.READ,
    "switch_tab": RiskLevel.READ,
    "fill": RiskLevel.WRITE,
    "upload": RiskLevel.WRITE,
    "download": RiskLevel.WRITE,
    "click": RiskLevel.WRITE,          # generic click; caller may override
    # windows
    "list_windows": RiskLevel.READ,
    "read_tree": RiskLevel.READ,
    "get_value": RiskLevel.READ,
    "find_control": RiskLevel.READ,
    "focus": RiskLevel.READ,
    "set_text": RiskLevel.WRITE,
    "invoke": RiskLevel.WRITE,
    "type_text": RiskLevel.WRITE,
    # explicitly destructive
    "delete": RiskLevel.DESTRUCTIVE,
    "overwrite": RiskLevel.DESTRUCTIVE,
    "pay": RiskLevel.DESTRUCTIVE,
    "submit_irreversible": RiskLevel.DESTRUCTIVE,
    "send_external": RiskLevel.DESTRUCTIVE,
    "kill_process": RiskLevel.DESTRUCTIVE,
}


@dataclass
class RiskDecision:
    action: str
    level: RiskLevel
    requires_confirmation: bool


def classify(action: str, override: str | None = None) -> RiskDecision:
    """Declare risk for an action. `override` lets the task raise (never lower)
    the level, e.g. a click that submits a payment."""
    if override and override in RiskLevel.__members__:
        level = RiskLevel(override)
    else:
        level = RISK_MAP.get(action, RiskLevel.WRITE)  # unknown defaults to WRITE
    return RiskDecision(action, level, level in (RiskLevel.WRITE, RiskLevel.DESTRUCTIVE))
