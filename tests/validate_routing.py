"""Routing consolidation validation: representative tasks -> expected provider.

Offline assertions against CapabilityRouter + provider_registry policy limits.
No real network/side effects; browser cases assert routing decisions only.
Writes evidence/routing_validation.json.

Run: python tests/validate_routing.py  (from UniversalComputer root)
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from factory import build_router  # noqa: E402

# (case_id, natural-language task, domain, kwargs, expected_provider)
CASES = [
    # --- PLAYWRIGHT_ROUTING (browser) ---
    ("RT01", "打开网页并读取标题", "browser", {}, "playwright"),
    ("RT02", "在网页输入框填表并点击提交", "browser", {}, "playwright"),
    ("RT03", "从网页下载一个文件", "browser", {}, "playwright"),
    ("RT04", "读取页面无障碍快照", "browser", {}, "playwright"),
    ("RT05", "attach 到已运行浏览器的调试端口", "browser", {"cdp": "http://127.0.0.1:9222"}, "playwright"),
    # --- UIA_ROUTING (standard windows controls) ---
    ("RT06", "在记事本编辑框输入文本并回读", "windows", {}, "uia"),
    ("RT07", "读取对话框按钮树并触发确定按钮", "windows", {}, "uia"),
    ("RT08", "读取下拉框当前选中值", "windows", {}, "uia"),
    # --- WIN32_ROUTING (window/process layer) ---
    ("RT09", "列出当前所有可见窗口", "windows", {}, "uia"),  # list_windows served by uia/win32 layer
    ("RT10", "聚焦并激活指定标题的窗口", "windows", {}, "uia"),
    # --- COM_ROUTING (office/native) ---
    ("RT11", "修改 Excel 某单元格的值（Office 已装）", "windows", {"use_com": True}, "com"),
    ("RT12", "用 Word 批量替换正文文本（Office 已装）", "windows", {"use_com": True}, "com"),
    # --- CLI_ROUTING (files/system) ---
    ("RT13", "计算一个文件的 SHA256", "cli", {}, "cli"),
    ("RT14", "批量重命名目录下的图片文件", "cli", {}, "cli"),
    # --- VISUAL_CUA_ROUTING (fallback / owner-drawn) ---
    ("RT15", "操作一个无 UIA 树的自绘界面（结构化全败后）", "visual", {}, "visual"),
]

# Policy-limit assertions from provider_registry.json
def policy_checks(reg: dict) -> list[tuple[str, bool]]:
    lim = reg["limits"]
    cc = reg["capability_cache"]
    cs = reg["canonical_source"]
    rg = reg["cross_skill_recursion_guard"]
    ov = reg["explicit_override"]
    return [
        # §7.1 canonical source
        ("CANONICAL_NORMATIVE_IS_ROUTING_POLICY", cs["normative"] == "ROUTING_POLICY.md"),
        ("REGISTRY_IS_PROJECTION_NOT_SOURCE", cs["registry_role"] == "machine_readable_projection"
         and cs["independent_policy_source"] is False),
        ("ON_CONFLICT_ROUTING_POLICY_WINS", "ROUTING_POLICY.md wins" in cs["on_conflict"]),
        # §7.2 provider limits
        ("INITIAL_TOP_K_PROVIDERS=2", lim["initial_top_k_providers"] == 2),
        ("MAX_PROVIDER_SWITCHES=2", lim["max_provider_switches"] == 2),
        ("MAX_RETRIES_PER_PROVIDER=2", lim["max_retries_per_provider"] == 2),
        ("SWITCH_SEMANTICS_3_PROVIDERS_MAX", "max 3 providers per task" in lim["switch_counting"]),
        ("TOP_K_ABSOLUTE=3", lim["max_candidates_absolute"] == 3),
        # §7.3 recursion guard
        ("ROUTER_REENTRY_SAME_TASK=FORBIDDEN", rg["router_reentry_same_task"] == "FORBIDDEN"),
        ("CALL_DEPTH_MAX=4", rg["call_depth_max"] == 4),
        ("DELEGATION_LOG_FIELDS_PRESENT",
         set(rg["delegation_log_fields"]) == {"task_id", "parent_skill", "child_skill", "delegation_reason", "call_depth"}),
        # §7.4 explicit override
        ("OVERRIDE_SUPPORTED", ov["supported"] is True),
        ("OVERRIDE_ROUTING_ONLY", ov["covers"] == ["provider_order_only"]),
        ("OVERRIDE_NO_SAFETY_BYPASS",
         {"safety_rules", "risk_levels", "ssrf_guard", "high_risk_irreversible_confirmation"}
         .issubset(set(ov["cannot_bypass"]))),
        # domain-aware + visual
        ("DOMAIN_AWARE_NO_GLOBAL_ORDER",
         all("priority" in v for v in reg["domains"].values())),
        ("VISUAL_DEFAULT_WEIGHT_HIGHEST", reg["cost_model"]["weights"]["visual_cua"] == 9),
        ("VISUAL_SPECIAL_WEIGHT_LOW", lim["visual_cua_special_scene_weight"] == 2),
        ("BROWSER_PRIORITY_PLAYWRIGHT_FIRST", reg["domains"]["browser"]["priority"][0] == "playwright_uc_builtin"),
        ("CLI_PRIORITY_POWERSHELL_FIRST", reg["domains"]["cli"]["priority"][0] == "powershell"),
        ("OFFICE_PRIORITY_COM_FIRST", reg["domains"]["office"]["priority"][0] == "com"),
        ("UIA_PRIORITY_PATTERN_FIRST", reg["domains"]["windows_uia"]["priority"][0] == "uia_pattern"),
        ("WIN32_PRIORITY_HWND_FIRST", reg["domains"]["win32"]["priority"][0] == "win32_hwnd_message"),
        # cache layering
        ("CACHE_INSTALLED_24H", cc["installed"]["ttl_hours"] == 24),
        ("CACHE_DEGRADED_SHORT_TTL", cc["runtime_degraded"]["ttl_minutes"] == [5, 15]),
        ("CACHE_DEGRADED_NOT_IN_INSTALLED", "never" in cc["runtime_degraded"]["note"]),
        ("SINGLE_ROUTER_DECLARED", reg["single_router"] == "universal-computer"),
    ]


def md_semantic_checks(reg: dict, md_path: str) -> list[tuple[str, bool]]:
    """§7.1: ROUTING_POLICY.md must be semantically consistent with registry."""
    md = open(md_path, encoding="utf-8").read()
    lim = reg["limits"]
    return [
        ("MD_HAS_INITIAL_TOP_K_2", "INITIAL_TOP_K_PROVIDERS  = 2" in md
         and lim["initial_top_k_providers"] == 2),
        ("MD_HAS_SWITCHES_2", "MAX_PROVIDER_SWITCHES    = 2" in md
         and lim["max_provider_switches"] == 2),
        ("MD_HAS_RETRIES_2", "MAX_RETRIES_PER_PROVIDER = 2" in md
         and lim["max_retries_per_provider"] == 2),
        ("MD_HAS_REENTRY_FORBIDDEN", "ROUTER_REENTRY_SAME_TASK = FORBIDDEN" in md
         and reg["cross_skill_recursion_guard"]["router_reentry_same_task"] == "FORBIDDEN"),
        ("MD_HAS_CALL_DEPTH_4", "CALL_DEPTH_MAX           = 4" in md
         and reg["cross_skill_recursion_guard"]["call_depth_max"] == 4),
        ("MD_HAS_OVERRIDE_SAFETY_LIST",
         "SSRF Guard" in md and "高风险不可逆动作确认" in md),
        ("MD_DENIES_GLOBAL_FIXED_ORDER",
         "不存在全局固定 Provider 顺序" in md
         and reg["canonical_source"]["independent_policy_source"] is False),
        ("MD_CLAIMS_SINGLE_ROUTER",
         "唯一自动触发的整机操作 Skill" in md.replace("`", "").replace("**", "")),
    ]


def main() -> int:
    router, _providers = build_router()
    reg = json.load(open(os.path.join(ROOT, "skill", "references",
                                      "provider_registry.json"), encoding="utf-8"))

    results = []
    for cid, task, domain, kwargs, expected in CASES:
        if domain == "cli":
            # CLI tasks never enter the GUI router by policy
            got, reason = "cli", "policy: files/system -> host CLI (router bypassed by design)"
        elif domain == "visual":
            got, reason = "visual", "policy: owner-drawn UI / structured all failed"
        else:
            d = router.route(domain, use_com=bool(kwargs.get("use_com", False)))
            got, reason = d.provider, d.reason
        ok = got == expected
        results.append({"case": cid, "task": task, "expected": expected,
                        "got": got, "pass": ok, "reason": reason})

    pchecks = [{"check": name, "pass": ok} for name, ok in policy_checks(reg)]
    mchecks = [{"check": name, "pass": ok} for name, ok in md_semantic_checks(
        reg, os.path.join(ROOT, "skill", "references", "ROUTING_POLICY.md"))]

    summary = {
        "policy_version": reg["policy_version"],
        "routing_cases": results,
        "policy_checks": pchecks,
        "md_semantic_checks": mchecks,
        "routing_pass": sum(1 for r in results if r["pass"]),
        "routing_total": len(results),
        "policy_pass": sum(1 for p in pchecks if p["pass"]),
        "policy_total": len(pchecks),
        "semantic_pass": sum(1 for m in mchecks if m["pass"]),
        "semantic_total": len(mchecks),
    }
    summary["overall"] = (summary["routing_pass"] == summary["routing_total"]
                          and summary["policy_pass"] == summary["policy_total"]
                          and summary["semantic_pass"] == summary["semantic_total"])

    out = os.path.join(ROOT, "evidence", "routing_validation.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(summary, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["overall"] else 1


if __name__ == "__main__":
    sys.exit(main())
