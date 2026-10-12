"""universal-computer CLI — the single stable entry point.

Any agent that can spawn a process and parse JSON on stdout can drive the
entire system. All subcommands print exactly one JSON document.

  python uc.py capabilities
  python uc.py run task.json
  python uc.py browser open --url https://...
  python uc.py windows list
  python uc.py inspect window --name "Notepad"
  python uc.py doctor
"""
from __future__ import annotations

import argparse
import json
import sys


def _json_print(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _build(args):
    from factory import build_router, build_runner
    router, providers = build_router(
        webmcp_enabled=args.webmcp,
        visual_enabled=args.visual,
        browser_headless=not args.headed,
        browser_profile_dir=args.profile,
        browser_cdp_endpoint=args.cdp,
    )
    runner = build_runner(router, confirm_callback=None)
    return router, providers, runner


def cmd_capabilities(args) -> int:
    router, providers, _ = _build(args)
    report = router.detect_all(force=True)
    _json_print({"capabilities": report})
    return 0


def cmd_run(args) -> int:
    from core.runner import load_task
    _, _, runner = _build(args)
    task_def = load_task(args.task_file)
    result = runner.run(task_def)
    _json_print(result)
    return 0 if result.get("task", {}).get("status") == "SUCCESS" else 1


def cmd_doctor(args) -> int:
    router, providers, _ = _build(args)
    caps = router.detect_all(force=True)
    checks = {name: c["available"] for name, c in caps.items()}
    # live browser launch probe (heavier than detect; only in doctor)
    browser_live = False
    try:
        pw = providers["playwright"]
        r = pw.open("data:text/html,<h1>doctor-ok</h1>")
        browser_live = r.success and "doctor-ok" in (r.result or {}).get("title", "") \
            or r.success
        pw.close()
    except Exception:
        browser_live = False
    _json_print({
        "doctor": {
            "python": sys.version.split()[0],
            "capabilities": checks,
            "browser_live_launch": browser_live,
            "webmcp_optin": args.webmcp,
            "visual_enabled": args.visual,
        }
    })
    return 0


def cmd_browser(args) -> int:
    _, providers, _ = _build(args)
    pw = providers["playwright"]
    params = dict(vars(args).get("params") or {})
    if args.browser_cmd == "open":
        params = {"url": args.url}
    elif args.browser_cmd in ("read", "fill", "click"):
        params = {"selector": args.selector}
        if args.browser_cmd == "fill":
            params["value"] = args.value
    elif args.browser_cmd == "screenshot":
        params = {"path": args.path}
    elif args.browser_cmd == "switch_tab":
        params = {"index": args.index}
    res = pw.dispatch("list_tabs" if args.browser_cmd == "tabs"
                      else args.browser_cmd, params)
    _json_print(res.to_dict())
    # each CLI invocation owns its own session; release it before exiting
    pw.close()
    return 0 if res.success else 1


def cmd_windows(args) -> int:
    _, providers, _ = _build(args)
    uia = providers["uia"]
    params = {}
    if args.windows_cmd in ("read_tree", "find_control", "invoke", "set_text",
                            "get_value", "focus"):
        params["window"] = {"name": args.window_name,
                            "class_name": args.window_class}
    if args.windows_cmd == "read_tree":
        params["depth"] = args.depth
    if args.windows_cmd in ("find_control", "invoke", "set_text", "get_value"):
        params["criteria"] = json.loads(args.criteria) if args.criteria else {}
    if args.windows_cmd == "set_text":
        params["value"] = args.value
    res = uia.dispatch("list_windows" if args.windows_cmd == "list"
                       else args.windows_cmd, params)
    _json_print(res.to_dict())
    return 0 if res.success else 1


def cmd_inspect(args) -> int:
    _, providers, _ = _build(args)
    if args.inspect_target == "window":
        uia = providers["uia"]
        res = uia.read_tree({"name": args.name, "class_name": args.wclass},
                            depth=args.depth)
        _json_print(res.to_dict())
        return 0 if res.success else 1
    if args.inspect_target == "site":
        pw = providers["playwright"]
        out = []
        if args.url:
            r = pw.open(args.url)
            out.append(r.to_dict())
        snap = pw.snapshot()
        out.append(snap.to_dict())
        pw.close()
        _json_print({"inspect": out})
        return 0
    _json_print({"error": "unknown inspect target"})
    return 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="universal-computer")
    ap.add_argument("--headed", action="store_true",
                    help="run browser headed instead of headless")
    ap.add_argument("--profile", default=None,
                    help="browser persistent profile dir (login state)")
    ap.add_argument("--cdp", default=None,
                    help="attach to running browser via CDP endpoint")
    ap.add_argument("--webmcp", action="store_true",
                    help="opt-in experimental WebMCP detection (default off)")
    ap.add_argument("--visual", action="store_true",
                    help="allow visual provider as fallback (default off)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("capabilities").set_defaults(fn=cmd_capabilities)

    p_run = sub.add_parser("run")
    p_run.add_argument("task_file")
    p_run.set_defaults(fn=cmd_run)

    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)

    p_b = sub.add_parser("browser")
    bsub = p_b.add_subparsers(dest="browser_cmd", required=True)
    b_open = bsub.add_parser("open"); b_open.add_argument("--url", required=True)
    b_read = bsub.add_parser("read"); b_read.add_argument("--selector", required=True)
    b_fill = bsub.add_parser("fill"); b_fill.add_argument("--selector", required=True)
    b_fill.add_argument("--value", required=True)
    b_click = bsub.add_parser("click"); b_click.add_argument("--selector", required=True)
    b_shot = bsub.add_parser("screenshot"); b_shot.add_argument("--path", required=True)
    bsub.add_parser("tabs")
    b_sw = bsub.add_parser("switch_tab"); b_sw.add_argument("--index", type=int, required=True)
    bsub.add_parser("close")
    p_b.set_defaults(fn=cmd_browser)

    p_w = sub.add_parser("windows")
    wsub = p_w.add_subparsers(dest="windows_cmd", required=True)
    wsub.add_parser("list")
    for name, extra in [
        ("read_tree", ["--depth"]),
        ("find_control", ["--criteria"]),
        ("invoke", ["--criteria"]),
        ("set_text", ["--criteria", "--value"]),
        ("get_value", ["--criteria"]),
        ("focus", []),
    ]:
        p = wsub.add_parser(name)
        p.add_argument("--window-name", default=None)
        p.add_argument("--window-class", default=None)
        if "--depth" in extra:
            p.add_argument("--depth", type=int, default=4)
        if "--criteria" in extra:
            p.add_argument("--criteria", default="{}")
        if "--value" in extra:
            p.add_argument("--value", required=True)
    p_w.set_defaults(fn=cmd_windows)

    p_i = sub.add_parser("inspect")
    isub = p_i.add_subparsers(dest="inspect_target", required=True)
    p_iw = isub.add_parser("window")
    p_iw.add_argument("--name", default=None)
    p_iw.add_argument("--wclass", default=None)
    p_iw.add_argument("--depth", type=int, default=3)
    p_is = isub.add_parser("site")
    p_is.add_argument("--url", default=None)
    p_i.set_defaults(fn=cmd_inspect)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
