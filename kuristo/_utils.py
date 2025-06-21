import sys
import subprocess
import os
import yaml
from .scanner import Scanner
from .test_spec import TestSpec
from jinja2 import Template


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


def resolve_path(path_str, source_root, build_root):
    """
    Resolve path
    """

    if os.path.isabs(path_str):
        return path_str

    if path_str.startswith("source:"):
        rel_path = path_str[len("source:") :]
        return os.path.join(source_root, rel_path)

    if path_str.startswith("build:"):
        rel_path = path_str[len("build:") :]
        return os.path.join(build_root, rel_path)

    # Heuristic fallback
    candidate = os.path.join(build_root, path_str)
    if os.path.exists(candidate):
        return candidate
    candidate = os.path.join(source_root, path_str)
    if os.path.exists(candidate):
        return candidate

    raise FileNotFoundError(f"Could not resolve path: {path_str}")


def rich_job_name(job_name):
    return job_name.replace("[", "\\[")


def interpolate_str(text: str, variables: dict) -> str:
    normalized = text.replace("${{", "{{").replace("}}", "}}")
    template = Template(normalized)
    return template.render(**variables)
