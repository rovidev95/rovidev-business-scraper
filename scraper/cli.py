from __future__ import annotations

import argparse
import asyncio
import logging

from .config import get_settings, load_sources
from .fetcher import HttpxFetcher
from .models import ChangeSet, SourceSpec
from .pipeline import DisallowedByRobots, ScrapePipeline
from .rate_limit import RateLimiter
from .sinks import CsvSink, JsonSink, Sink
from .state import JsonStateStore


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="business-scraper",
        description="Scrape configured sources, detect changes and export the results.",
    )
    parser.add_argument("--sources", required=True, help="Path to a JSON file of source specs.")
    parser.add_argument("--json", dest="json_out", help="Write items + changes to this JSON file.")
    parser.add_argument("--csv", dest="csv_out", help="Write items to this CSV file.")
    parser.add_argument("--no-robots", action="store_true", help="Skip robots.txt checks.")
    parser.add_argument("--no-state", action="store_true", help="Do not diff against past runs.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable info logging.")
    return parser


def _print_summary(spec: SourceSpec, count: int, changes: ChangeSet | None) -> None:
    print(f"\n{spec.name}: {count} items")
    if changes is None:
        return
    if changes.is_empty:
        print("  no changes since last run")
        return
    if changes.added:
        print(f"  + {len(changes.added)} new")
    if changes.removed:
        print(f"  - {len(changes.removed)} gone")
    for change in changes.price_changes:
        delta = change.delta
        arrow = "→" if delta is None else ("↑" if delta > 0 else "↓")
        print(f"  {arrow} {change.title}: {change.old_price} {arrow} {change.new_price}")
    for item in changes.back_in_stock:
        print(f"  ✓ back in stock: {item.title}")
    for item in changes.out_of_stock:
        print(f"  ✗ out of stock: {item.title}")


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()
    specs = load_sources(args.sources)

    fetcher = HttpxFetcher(timeout=settings.timeout)
    pipeline = ScrapePipeline(
        fetcher,
        rate_limiter=RateLimiter(settings.min_interval),
        respect_robots=settings.respect_robots and not args.no_robots,
        default_user_agent=settings.user_agent,
    )
    store = None if args.no_state else JsonStateStore(settings.state_dir)

    sinks: list[Sink] = []
    if args.json_out:
        sinks.append(JsonSink(args.json_out))
    if args.csv_out:
        sinks.append(CsvSink(args.csv_out))

    exit_code = 0
    for spec in specs:
        try:
            items, changes = await pipeline.run(spec, store=store, sinks=sinks)
            _print_summary(spec, len(items), changes)
        except DisallowedByRobots as exc:
            print(f"\n{spec.name}: skipped ({exc})")
            exit_code = 1
    return exit_code


def main() -> None:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
