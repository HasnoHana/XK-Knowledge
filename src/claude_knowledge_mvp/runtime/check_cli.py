from __future__ import annotations

import argparse
import json
from pathlib import Path

from claude_knowledge_mvp.runtime.check import execute_check, prepare_check_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xk-check-runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--repo-root", required=True)
    run_parser.add_argument("--wiki-path", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--repo-root", required=True)
    prepare_parser.add_argument("--wiki-path", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        result = execute_check(repo_root=Path(args.repo_root), wiki_relative_path=args.wiki_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "prepare":
        payload = prepare_check_payload(repo_root=Path(args.repo_root), wiki_relative_path=args.wiki_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
