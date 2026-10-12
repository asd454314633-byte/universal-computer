#!/usr/bin/env python
"""universal-computer launcher: python uc.py <subcommand> [--options]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli"))

from cli.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
