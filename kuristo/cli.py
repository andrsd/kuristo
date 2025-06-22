import argparse
from kuristo import __version__


def build_cli():
    parser = argparse.ArgumentParser(prog="kuristo", description="Kuristo automation framework")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run jobs")
    run_parser.add_argument("--location", "-l", action="append", help="Location to scan for workflow files")
    run_parser.add_argument("--verbose", "-v", type=int, default=0, help="Verbose level")

    # Doctor command
    subparsers.add_parser("doctor", help="Show diagnostic info")

    # List command
    list_parser = subparsers.add_parser("list", help="List available jobs")
    list_parser.add_argument("--location", "-l", action="append", help="Location to scan for workflow files")

    return parser
