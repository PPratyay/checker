"""Shared command-line runner for individual guideline checkers."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from typing import NoReturn


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "coding-guidelines-checker.py"
SPEC = importlib.util.spec_from_file_location("coding_guidelines_checker", CHECKER_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load {CHECKER_PATH}")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def run(category: str, description: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--clang-arg", action="append", default=[])
    parser.add_argument("--write-comments", action="store_true")
    args = parser.parse_args(argv)
    exit_code = 0
    for source in args.files:
        try:
            findings = checker.check_category(source, category, args.clang_arg)
            if args.write_comments:
                checker.write_review_comments(source, findings)
            else:
                for finding in findings:
                    print(f"{source}:{finding}")
        except (OSError, checker.cindex.LibclangError, ValueError) as error:
            print(f"{source}: error: {error}", file=sys.stderr)
            exit_code = 2
            continue
        exit_code = max(exit_code, min(len(findings), 1))
    return exit_code
