import sys
import argparse
import yaml
from datetime import datetime
from pathlib import Path
from .config import Config
from .scanner import Scanner
from .test_spec import TestSpec
from .scheduler import Scheduler
from .resources import Resources
from .action_factory import ActionFactory
from .actions.mpi_action import MPIAction
from .actions.seq_action import SeqAction
from ._plugin_loader import load_user_steps_from_kuristo_dir


def register_actions():
    ActionFactory.register("core/sequential", SeqAction)
    ActionFactory.register("core/mpi", MPIAction)


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Test framework")
    parser.add_argument("--location", "-l", action="append", type=str, help="Location to scan for test specifications")
    parser.add_argument("--verbose", "-v", type=int, help="Verbose level")
    return parser


def scan_locations(locations):
    """
    Scan the locations for the test specification files
    """
    spec_files = []
    for loc in locations:
        scanner = Scanner(loc)
        spec_files.extend(scanner.scan())
    return spec_files


def tests_from_file(file_path):
    test_specs = []
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
        tests = data.get('tests', {})
        for t, params in tests.items():
            test_specs.append(TestSpec.from_dict(t, params))
    return test_specs


def parse_tests_files(spec_files):
    """
    Parse test files (ktests.yaml)
    """
    tests = []
    for file in spec_files:
        tests.extend(tests_from_file(file))
    return tests


def create_run_output_dir(base_log_dir: Path) -> Path:
    runs_dir = base_log_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = runs_dir / timestamp
    run_dir.mkdir()
    return run_dir


def update_latest_symlink(base_log_dir: Path, latest_run_dir: Path):
    """
    Create or update a symlink named 'latest' inside base_log_dir that points to latest_run_dir.
    """
    latest_link = base_log_dir / "runs" / "latest"
    print(latest_link)
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    relative_target = latest_run_dir.relative_to(base_log_dir / "runs")
    latest_link.symlink_to(relative_target, target_is_directory=True)


def main():
    config = Config()
    log_dir = create_run_output_dir(config.log_dir)
    update_latest_symlink(config.log_dir, log_dir)

    register_actions()
    load_user_steps_from_kuristo_dir()

    parser = build_arg_parser()
    args = parser.parse_args()
    if args.location is None:
        sys.exit("Must specify at least one location")

    tests_files = scan_locations(args.location)
    tests = parse_tests_files(tests_files)
    rcs = Resources()
    scheduler = Scheduler(tests, rcs, log_dir)
    scheduler.check()
    scheduler.run_all_jobs()


if __name__ == "__main__":
    main()
