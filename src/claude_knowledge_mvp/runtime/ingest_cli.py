from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from claude_knowledge_mvp.runtime.ingest import commit_ingest_artifacts, execute_ingest, execute_ingest_debug, prepare_ingest_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xk-ingest-runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--repo-root", required=True)
    run_parser.add_argument("--raw-path", required=True)
    run_parser.add_argument("--mutation-json")

    debug_run_parser = subparsers.add_parser("debug-run")
    debug_run_parser.add_argument("--repo-root", required=True)
    debug_run_parser.add_argument("--raw-path", required=True)
    debug_run_parser.add_argument("--mutation-json")

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--repo-root", required=True)
    prepare_parser.add_argument("--raw-path", required=True)

    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("--repo-root", required=True)
    commit_parser.add_argument("--mutation-json", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        result = execute_ingest(
            repo_root=Path(args.repo_root),
            raw_relative_path=args.raw_path,
            mutation_json_path=Path(args.mutation_json) if args.mutation_json else None,
        )
        output = asdict(result) if is_dataclass(result) else result
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if args.command == "debug-run":
        output = execute_ingest_debug(
            repo_root=Path(args.repo_root),
            raw_relative_path=args.raw_path,
            mutation_json_path=Path(args.mutation_json) if args.mutation_json else None,
        )
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if args.command == "prepare":
        payload = prepare_ingest_payload(
            repo_root=Path(args.repo_root),
            raw_relative_path=args.raw_path,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "commit":
        result = commit_ingest_artifacts(
            repo_root=Path(args.repo_root),
            mutation_json_path=Path(args.mutation_json),
        )
        output = asdict(result) if is_dataclass(result) else result
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
