import sys
import subprocess
import os
import yaml
from .scanner import Scanner
from .test_spec import TestSpec


def get_default_core_limit():
    if sys.platform == "darwin":
        try:
            # Apple Silicon: performance cores
            output = subprocess.check_output(
                ["sysctl", "-n", "hw.perflevel0.physicalcpu"],
                text=True
            )
            perf_cores = int(output.strip())
            return max(perf_cores, 1)
        except Exception:
            pass  # fallback below
    return os.cpu_count() or 1


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
