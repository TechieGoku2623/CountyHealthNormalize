"""Command-line interface for CountyHealthNormalize."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from county_health_normalize import __version__
from county_health_normalize.config import get_settings
from county_health_normalize.errors import CountyHealthNormalizeError
from county_health_normalize.pipeline import normalize_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chn",
        description="Normalize county health datasets into a canonical schema.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    normalize = sub.add_parser("normalize", help="Normalize a CSV file")
    normalize.add_argument("input", type=Path, help="Path to raw CSV input")
    normalize.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path for normalized CSV output (default: data/processed/<input>.csv)",
    )
    normalize.add_argument(
        "--source",
        default=None,
        help="Adapter name (default: settings / generic_csv)",
    )
    normalize.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Fail on invalid rows (default from CHN_STRICT)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "normalize":
        source = args.source or settings.default_source
        strict = settings.strict if args.strict is None else args.strict
        output = args.output or (settings.output_dir / f"{args.input.stem}.normalized.csv")
        try:
            result = normalize_csv(args.input, output, source=source, strict=strict)
        except CountyHealthNormalizeError as exc:
            logging.error("%s", exc)
            return 1
        print(f"normalized {len(result)} rows -> {output}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
