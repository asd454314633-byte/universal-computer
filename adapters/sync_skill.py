"""Sync canonical skill package to all host skill directories.

Canonical source: UniversalComputer/skill/  (the ONLY place to edit)
Host copies (generated, never hand-edited):
  - WorkBuddy : ~/.workbuddy/skills/universal-computer/
  - Qoder CN  : ~/.qoder-cn/skills/universal-computer/   (skip if junction)
  - Codex     : ~/.codex/skills/universal-computer/      (junction to canonical supported)

A host dir that is a junction/symlink to the canonical skill/ (or to another
synced host) is never copy-synced through: rmtree through a link is
fail-safe (OSError) on Python >=3.13 but destructive on older runtimes.

Usage:
  python adapters/sync_skill.py                 # sync all hosts
  python adapters/sync_skill.py --target codex  # one host
  python adapters/sync_skill.py --check         # verify only
  python adapters/sync_skill.py --canonical <path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

CANONICAL = Path(__file__).resolve().parent.parent / "skill"
SYNC_MARKER = ".universal-computer-synced.json"
HOME = Path.home()

HOSTS = {
    "workbuddy": HOME / ".workbuddy" / "skills" / "universal-computer",
    "qoder": HOME / ".qoder-cn" / "skills" / "universal-computer",
    "codex": HOME / ".codex" / "skills" / "universal-computer",
}


def is_junction(p: Path) -> bool:
    # Protect both symbolic links and Windows junctions from replacement.
    if p.is_symlink():
        return True
    if hasattr(os.path, "isjunction"):
        return os.path.isjunction(str(p))
    try:
        return p.exists() and os.path.realpath(str(p)) != str(p.resolve())
    except OSError:
        return False


def same_junction_target(a: Path, b: Path) -> bool:
    """True if a and b resolve to the same real directory (junction/alias)."""
    try:
        ra = Path(os.path.realpath(str(a)))
        rb = Path(os.path.realpath(str(b)))
        # realpath may not expand mount-point junctions for the leaf dir;
        # compare via a probe file inside each directory as a fallback.
        if ra == rb:
            return True
        probe = f"__uc_probe_{os.getpid()}.tmp"
        (a / probe).write_text("x", encoding="utf-8")
        hit = (b / probe).exists()
        (a / probe).unlink(missing_ok=True)
        return hit
    except OSError:
        return False


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    # Generated per-host files are excluded from the canonical comparison.
    return {
        str(f.relative_to(root)).replace("\\", "/"): sha256(f)
        for f in sorted(root.rglob("*"))
        if f.is_file() and f.name not in ("core_path.txt", SYNC_MARKER)
    }


def sync(host: str, dest: Path, canonical: Path, check: bool) -> dict:
    # Any host dir that is itself a junction/link is never copy-synced through.
    # Live-linked to canonical -> nothing to do; unrelated link -> refuse loudly.
    if is_junction(dest):
        if same_junction_target(dest, canonical):
            return {"host": host, "status": "ALIAS_OF_CANONICAL",
                    "dest": str(dest), "files": len(snapshot(dest)),
                    "note": "dir is a junction to canonical skill/; live-linked, no sync needed"}
        return {"host": host, "status": "JUNCTION_UNRELATED",
                "dest": str(dest),
                "note": "junction does not point at canonical; inspect manually"}

    # Qoder CN skills dir is a junction to workbuddy skills on this machine:
    # syncing twice to the same real dir is harmless but redundant.
    if host == "qoder" and same_junction_target(dest.parent.parent,
                                                HOSTS["workbuddy"].parent.parent):
        return {"host": host, "status": "ALIAS_OF_WORKBUDDY",
                "dest": str(dest), "note": "skills dir is a junction to ~/.workbuddy/skills"}

    want = snapshot(canonical)
    if check:
        if not dest.exists():
            return {"host": host, "status": "MISSING", "dest": str(dest)}
        have = snapshot(dest)
        return {"host": host, "status": "MATCH" if have == want else "DRIFT",
                "dest": str(dest)}

    # Refuse to remove unknown or manually changed Skill directories.
    if dest.exists():
        have = snapshot(dest)
        marker = dest / SYNC_MARKER
        if marker.is_file():
            try:
                manifest = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                manifest = {}
            owned_and_unchanged = (
                manifest.get("managed_by") == "universal-computer/sync_skill.py"
                and manifest.get("files") == have
            )
        else:
            # Adopt old copies only when their files match the canonical Skill.
            owned_and_unchanged = have == want
        if not owned_and_unchanged:
            return {"host": host, "status": "PROTECTED_EXISTING",
                    "dest": str(dest),
                    "note": "unknown or modified Skill; nothing was deleted"}
        shutil.rmtree(dest)
    shutil.copytree(canonical, dest)
    (dest / "scripts" / "core_path.txt").write_text(
        str(canonical.parent), encoding="utf-8")
    have = snapshot(dest)
    (dest / SYNC_MARKER).write_text(
        json.dumps({"managed_by": "universal-computer/sync_skill.py",
                    "files": have}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return {"host": host, "status": "SYNCED" if have == want else "FAIL",
            "dest": str(dest), "files": len(have)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", default=str(CANONICAL))
    ap.add_argument("--target", choices=[*HOSTS, "all"], default="all")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    canonical = Path(args.canonical).resolve()
    if not (canonical / "SKILL.md").exists():
        print(json.dumps({"success": False,
                          "error": f"no SKILL.md under {canonical}"}))
        return 2

    targets = HOSTS.items() if args.target == "all" else [(args.target, HOSTS[args.target])]
    results = [sync(h, d, canonical, args.check) for h, d in targets]
    ok = all(r["status"] in ("SYNCED", "MATCH", "ALIAS_OF_WORKBUDDY",
                             "ALIAS_OF_CANONICAL") for r in results)
    print(json.dumps({"success": ok, "canonical": str(canonical),
                      "results": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
