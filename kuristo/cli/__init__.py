import argparse
from pathlib import Path
from kuristo._version import __version__
from kuristo.cli._run import run_jobs
from kuristo.cli._doctor import print_diag
from kuristo.cli._list import list_jobs
from kuristo.cli._batch import batch
from kuristo.cli._status import status
from kuristo.cli._log import log
from kuristo.cli._show import show
from kuristo.cli._report import report


__all__ = [
    "__version__",
    "run_jobs",
    "print_diag",
    "list_jobs",
    "batch",
    "status",
    "log",
    "show",
    "report"
]


def build_parser():
    parser = argparse.ArgumentParser(prog="kuristo", description="Kuristo automation framework")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-ansi", action="store_true", help="Disable rich output (no colors or progress bars)")
    parser.add_argument("-f", "--config", type=Path, metavar="FILE", help="Path to configuration file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run jobs")
    run_parser.add_argument("--verbose", "-v", type=int, default=0, help="Verbose level")
    run_parser.add_argument("locations", nargs="*", help="Locations to scan for workflow files")

    # Doctor command
    subparsers.add_parser("doctor", help="Show diagnostic info")

    # List command
    list_parser = subparsers.add_parser("list", help="List available jobs")
    list_parser.add_argument("locations", nargs="*", help="Locations to scan for workflow files")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="HPC queueing system commands")
    batch_subparsers = batch_parser.add_subparsers(dest="batch_command")

    batch_submit_parser = batch_subparsers.add_parser("submit", help="Submit jobs to HPC queue")
    batch_submit_parser.add_argument("--backend", type=str, help="Batch backend to use: ['slurm']")
    batch_submit_parser.add_argument("--partition", type=str, help="Partition name to use")
    batch_submit_parser.add_argument("locations", nargs="*", help="Locations to scan for workflow files")

    batch_subparsers.add_parser("status", help="Check HPC job status")

    batch_run_parser = batch_subparsers.add_parser("run", help="Run job in a batch system")
    batch_run_parser.add_argument("run_id", help="ID of the run")
    batch_run_parser.add_argument("first_job_id", type=int, help="First job ID to start from")
    batch_run_parser.add_argument("workflow_file", help="Workflow file to run")

    # Status command
    status_parser = subparsers.add_parser("status", help="Display status of runs")
    status_parser.add_argument("--run-id", type=str, help="Run ID to display results for")
    group = status_parser.add_mutually_exclusive_group()
    group.add_argument("--failed", action="store_true", help="Show only tests that failed")
    group.add_argument("--skipped", action="store_true", help="Show only tests that were skipped")
    group.add_argument("--passed", action="store_true", help="Show only tests that passed")

    # Log command
    subparsers.add_parser("log", help="List runs")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show job log")
    show_parser.add_argument("--run-id", type=str, help="Run ID to display results for")
    show_parser.add_argument("--job", required=True, type=int, help="Job ID")

    # Report command
    report_parser = subparsers.add_parser("report", help="Create report")
    report_parser.add_argument("--run-id", type=str, help="Run ID to generate report for")
    group = report_parser.add_mutually_exclusive_group()
    group.add_argument("--failed", action="store_true", help="Show only tests that failed")
    group.add_argument("--skipped", action="store_true", help="Show only tests that were skipped")
    group.add_argument("--passed", action="store_true", help="Show only tests that passed")

    report_parser.add_argument("--output", help="File name to store the report into: <format>:<filename>")

    return parser
