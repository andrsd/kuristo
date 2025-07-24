import argparse
from pathlib import Path
from kuristo import __version__
from .run import run_jobs
from .doctor import print_diag
from .list import list_jobs
from .batch import batch


__all__ = [
    "run_jobs",
    "print_diag",
    "list_jobs",
    "batch"
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

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="HPC queueing system commands")
    batch_subparsers = batch_parser.add_subparsers(dest="batch_command")

    submit_parser = batch_subparsers.add_parser("submit", help="Submit jobs to HPC queue")
    submit_parser.add_argument("--location", "-l", action="append", help="Location to scan for workflow files")
    submit_parser.add_argument("--backend", type=str, help="Batch backend to use: ['slurm']")
    submit_parser.add_argument("--partition", type=str, help="Partition name to use")

    batch_subparsers.add_parser("status", help="Check HPC job status")

    return parser
