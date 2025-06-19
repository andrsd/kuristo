import argparse


def build_cli():
    parser = argparse.ArgumentParser(prog="kuristo", description="Kuristo test framework")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run test suite")
    run_parser.add_argument("--location", "-l", action="append", help="Location to scan for test specifications")
    run_parser.add_argument("--verbose", "-v", type=int, default=0, help="Verbose level")

    # Doctor command
    subparsers.add_parser("doctor", help="Show diagnostic info")

    # List command
    list_parser = subparsers.add_parser("list", help="List available test cases")
    list_parser.add_argument("--location", "-l", action="append", help="Location to scan for test specifications")

    return parser
