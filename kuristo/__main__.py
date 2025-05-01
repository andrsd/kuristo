import argparse
import logging
from .scanner import Scanner
from .test_spec import TestSpec
from .scheduler import Scheduler
from .resources import Resources


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


def parse_spec_files(spec_files):
    """
    Parse test specification files
    """
    tests = []
    for file in spec_files:
        tests.extend(TestSpec.from_file(file))
    return tests


def main():
    logging.basicConfig(level=logging.INFO)

    parser = build_arg_parser()
    args = parser.parse_args()
    if args.location is None:
        raise SystemExit("Must specify at least one location")

    spec_files = scan_locations(args.location)
    tests = parse_spec_files(spec_files)
    rcs = Resources()
    scheduler = Scheduler(tests, rcs)
    scheduler.check()
    scheduler.run_all_jobs()

if __name__ == "__main__":
    main()
