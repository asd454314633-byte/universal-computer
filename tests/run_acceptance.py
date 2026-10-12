"""Minimal real acceptance tests: B1-B4, R1-R3, F1 (browser + router +
recovery), plus W1-W4 (Windows UIA via Notepad fixture).

Each case writes an evidence JSON file into evidence/ and prints a verdict.
Run with the managed venv python from the project root:
    python tests/run_acceptance.py
"""
from __future__ import annotations

import http.server
import json
import os
import socket
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from factory import build_router, build_runner  # noqa: E402

EVIDENCE = os.path.join(ROOT, "evidence")
SITE_DIR = os.path.join(HERE, "fixtures", "site")
PY = sys.executable


# ---- helpers ---------------------------------------------------------------

def save_evidence(name: str, payload: dict) -> str:
    path = os.path.join(EVIDENCE, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    return path


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_site() -> tuple[int, object]:
    port = free_port()
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=SITE_DIR, **kw)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return port, srv


def new_providers(headless=True):
    router, providers = build_router(browser_headless=headless)
    return router, providers


# ---- B: browser primary path ----------------------------------------------

def browser_cases(port: int) -> dict:
    results = {}
    router, providers = new_providers(headless=True)
    pw = providers["playwright"]
    base = f"http://127.0.0.1:{port}/index.html"

    # B1: open page and read a named element
    r = pw.open(base)
    title = (r.result or {}).get("title", "")
    r2 = pw.read_text("#page-title")
    b1_text = (r2.result or {}).get("text", "")
    results["B1"] = r.success and r2.success and "订单确认" in b1_text and title == "UniversalComputer 验收测试站点"
    save_evidence("B1_open_read", {
        "open": r.to_dict(), "read": r2.to_dict(), "pass": results["B1"]})

    # B2: locate input by structure and fill
    r3 = pw.fill("#order-name", "验收用户")
    r4 = pw.evaluate("document.getElementById('order-name').value")
    b2_val = (r4.result or {}).get("value")
    results["B2"] = r3.success and b2_val == "验收用户"
    save_evidence("B2_fill_input", {
        "fill": r3.to_dict(), "verify": r4.to_dict(), "pass": results["B2"]})

    # B3: locate button semantically/structurally and click
    r5 = pw.click("#submit-order")
    r6 = pw.read_text("#results")
    b3_text = (r6.result or {}).get("text", "")
    results["B3"] = r5.success and "订单已提交：验收用户" in b3_text
    save_evidence("B3_click_button", {
        "click": r5.to_dict(), "result_text": r6.to_dict(), "pass": results["B3"]})

    # B4: layout + DOM hierarchy change, then still locate by structure
    r7 = pw.click("#toggle-layout")
    r8 = pw.fill("#order-name", "布局变化后")
    r9 = pw.click("#submit-order")
    r10 = pw.read_text("#results")
    b4_text = (r10.result or {}).get("text", "")
    results["B4"] = r7.success and r8.success and r9.success \
        and "订单已提交：布局变化后" in b4_text
    save_evidence("B4_layout_change", {
        "toggle": r7.to_dict(), "fill_after": r8.to_dict(),
        "click_after": r9.to_dict(), "result_text": r10.to_dict(),
        "pass": results["B4"]})

    # screenshot evidence of final state
    shot = os.path.join(EVIDENCE, "browser_final_state.png")
    pw.screenshot(shot)
    pw.close()
    results["screenshot"] = shot
    return results


# ---- R: router -------------------------------------------------------------

def router_cases() -> dict:
    results = {}
    router, providers = new_providers()

    # R1: browser task routes to playwright (structural path first)
    d1 = router.route("browser")
    results["R1"] = d1.provider == "playwright" and d1.ladder == \
        ["playwright", "visual"]
    save_evidence("R1_route_browser", {
        "decision": {"domain": d1.domain, "provider": d1.provider,
                     "reason": d1.reason, "ladder": d1.ladder},
        "pass": results["R1"]})

    # R2: windows standard-control task routes to UIA
    d2 = router.route("windows")
    results["R2"] = d2.provider == "uia" and d2.ladder == ["uia", "win32", "visual"]
    save_evidence("R2_route_windows", {
        "decision": {"domain": d2.domain, "provider": d2.provider,
                     "reason": d2.reason, "ladder": d2.ladder},
        "pass": results["R2"]})

    # R3: structural providers precede visual fallback, always in order.
    from providers.base import CapabilityInfo
    r3_pass = True

    # (a) uia unavailable -> next structural provider (win32) is used
    router2, _ = build_router()
    router2.providers["uia"].detect = lambda: CapabilityInfo(
        "uia", "windows", False, "forced unavailable", [])
    router2._detect_cache.clear()
    d3 = router2.route("windows")
    a_ok = d3.provider == "win32"

    # (b) uia + win32 both unavailable -> visual is the only candidate left,
    # and it is ONLY entered when explicitly enabled
    router3, _ = build_router()
    router3.providers["uia"].detect = lambda: CapabilityInfo(
        "uia", "windows", False, "forced unavailable", [])
    router3.providers["win32"].detect = lambda: CapabilityInfo(
        "win32", "windows", False, "forced unavailable", [])
    router3._detect_cache.clear()
    d4 = router3.route("windows")           # visual disabled -> none
    b_ok = d4.provider == "none"
    router3.visual_enabled = True
    d5 = router3.route("windows")           # visual enabled -> visual mock
    c_ok = d5.provider == "visual"

    results["R3"] = a_ok and b_ok and c_ok
    save_evidence("R3_fallback_order", {
        "normal_browser": {"provider": d1.provider, "ladder": d1.ladder},
        "normal_windows": {"provider": d2.provider, "ladder": d2.ladder},
        "uia_disabled": {"provider": d3.provider},
        "uia_win32_disabled_visual_off": {"provider": d4.provider},
        "uia_win32_disabled_visual_on": {"provider": d5.provider},
        "pass": results["R3"]})
    return results


# ---- F: recovery -----------------------------------------------------------

def recovery_case(port: int) -> dict:
    from core.recovery import run_with_recovery
    from core.protocol import ActionResult, ActionError

    router, providers = new_providers()
    pw = providers["playwright"]
    pw.open(f"http://127.0.0.1:{port}/index.html")

    attempts = {"n": 0}
    calls = []

    def attempt(is_retry: bool) -> ActionResult:
        attempts["n"] += 1
        calls.append({"attempt": attempts["n"], "is_retry": is_retry})
        if not is_retry:
            # simulate stale selector: element gone after re-render
            return ActionResult(False, "playwright", "fill",
                                {"selector": "#stale-input"}, None, [], 5,
                                ActionError("LOCATE_FAILED", "locate", True,
                                            True, "stale selector"), False)
        return pw.fill("#order-name", "恢复成功")

    result = run_with_recovery(pw, "fill", {"selector": "#order-name"}, attempt)
    pw.close()

    passed = (result.success and result.recovered and attempts["n"] == 2
              and len(calls) == 2)
    save_evidence("F1_recovery", {
        "attempts": calls,
        "final": result.to_dict(),
        "pass": passed})
    return {"F1": passed}


# ---- W: windows UIA primary path (self-owned Win32 fixture window) ----------

def windows_cases() -> dict:
    from tests.fixtures.win32_host import (WND_TITLE, WND_CLASS,
                                           BUTTON_RESULT_TEXT, start_fixture)
    results = {}
    router, providers = new_providers()
    uia = providers["uia"]

    stop = start_fixture()
    time.sleep(1.5)  # let the fixture window appear
    win = {"name": WND_TITLE, "class_name": WND_CLASS}
    try:
        # W1: recognize a real Windows window (our own fixture, zero user impact)
        r1 = uia.dispatch("list_windows", {})
        wins = (r1.result or {}).get("windows", [])
        match = [w for w in wins if WND_TITLE == w.get("Name")]
        results["W1"] = r1.success and len(match) >= 1
        save_evidence("W1_recognize_window", {
            "windows_found": [w.get("Name") for w in wins],
            "fixture_matches": match,
            "isolation": "window owned by the test process; no user app touched",
            "pass": results["W1"]})

        # W2: read the UIA control tree of a real window
        r2 = uia.read_tree(win, depth=3)
        tree_dump = json.dumps(r2.result or {}, default=str)
        results["W2"] = r2.success and "Edit" in tree_dump and "Button" in tree_dump
        save_evidence("W2_read_tree", {"tree": r2.result, "pass": results["W2"]})

        # W3: find a real control and act on it — set text via value pattern,
        # read it back, then invoke the button and observe the state change.
        edit_criteria = {"control_type": "edit", "search_depth": 5}
        r3 = uia.set_text(win, edit_criteria, "UNIVERSAL_UIA_ACCEPTANCE_2026")
        r3b = uia.get_value(win, edit_criteria)
        got = (r3b.result or {}).get("value", "")
        btn_criteria = {"control_type": "button", "search_depth": 5}
        r3c = uia.invoke(win, btn_criteria)
        time.sleep(0.4)
        r3d = uia.get_value(win, edit_criteria)
        after = (r3d.result or {}).get("value", "")
        results["W3"] = (r3.success and "UNIVERSAL_UIA_ACCEPTANCE_2026" in got
                         and r3c.success and after == BUTTON_RESULT_TEXT)
        save_evidence("W3_control_action", {
            "set_text": r3.to_dict(), "get_value": r3b.to_dict(),
            "invoke_button": r3c.to_dict(), "value_after_invoke": r3d.to_dict(),
            "pass": results["W3"]})

        # W4: prove not coordinate-based — locators were ControlType/Name/
        # ClassName only; record criteria used for the audit trail.
        r4 = uia.find_control(win, edit_criteria)
        found = (r4.result or {}).get("found", {})
        results["W4"] = r4.success and bool(found.get("ControlType"))
        save_evidence("W4_no_coordinates", {
            "locator": edit_criteria,
            "found_control": found,
            "note": "located via UIA structural properties; zero screen "
                    "coordinates involved",
            "pass": results["W4"]})
    finally:
        stop.set()  # fixture window closes with the daemon thread

    return results


# ---- main -------------------------------------------------------------------

def main() -> int:
    os.makedirs(EVIDENCE, exist_ok=True)
    port, srv = start_site()
    all_results: dict[str, bool] = {}
    try:
        print(f"[site] http://127.0.0.1:{port}/index.html")
        all_results.update(browser_cases(port))
        all_results.update(router_cases())
        all_results.update(recovery_case(port))
        all_results.update(windows_cases())
    finally:
        srv.shutdown()

    verdict = {k: ("PASS" if v else "FAIL") for k, v in all_results.items()
               if k.startswith(("B", "W", "R", "F"))}
    overall = all(v for k, v in all_results.items() if k.startswith(("B", "W", "R", "F")))
    save_evidence("acceptance_summary", {"verdicts": verdict, "overall": overall})
    print(json.dumps(verdict, indent=2))
    print("OVERALL:", "PASS" if overall else "FAIL")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
