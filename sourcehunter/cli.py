"""CLI: trace one claim, or run the 5-claim demo."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .api import FetchClient, ResearchClient
from .trace import to_json, trace

EXIT_OK, EXIT_USAGE, EXIT_FETCH = 0, 2, 3


def _key() -> str:
    k = os.getenv("TINYFISH_API_KEY", "")
    if not k:
        print(
            "error: TINYFISH_API_KEY not set (https://agent.tinyfish.ai/api-keys)",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_USAGE)
    return k


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Source Hunter: trace a claim to its original source."
    )
    ap.add_argument("claim", help="the claim/quote/statistic to trace")
    ap.add_argument("--mode", default="deep", choices=["deep", "max"])
    ap.add_argument(
        "--verify-top",
        type=int,
        default=12,
        help="how many citations to Fetch-verify (default 12)",
    )
    ap.add_argument("--output", help="write JSON to this file")
    ap.add_argument(
        "--version", action="version", version=f"source-hunter {__version__}"
    )
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    key = _key()
    t = trace(
        args.claim,
        ResearchClient(key),
        FetchClient(key),
        verify_top=args.verify_top,
        mode=args.mode,
    )
    text = to_json(t)
    if args.output:
        with open(args.output, "w") as f:
            f.write(text + "\n")
    print(text)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
