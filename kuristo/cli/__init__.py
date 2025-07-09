import argparse
from pathlib import Path
from kuristo import __version__
from .run import run_jobs
from .doctor import print_diag
from .list import list_jobs


__all__ = [
    "run_jobs",
    "print_diag",
    "list_jobs"
]


def build_parser():
    parser = argparse.ArgumentParser(prog="kuristo", description="Kuristo automation framework")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-ansi", action="store_true", help="Disable rich output (no colors or progress bars)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run jobs")
    run_parser.add_argument("--location", "-l", action="append", help="Location to scan for workflow files")
    run_parser.add_argument("--verbose", "-v", type=int, default=0, help="Verbose level")
    run_parser.add_argument("--report", type=Path, help="Save report with the runtime information to a CSV file")

    # Doctor command
    subparsers.add_parser("doctor", help="Show diagnostic info")

    # List command
    list_parser = subparsers.add_parser("list", help="List available jobs")
    list_parser.add_argument("--location", "-l", action="append", help="Location to scan for workflow files")

    return parser
