import sys
import subprocess
import os
import yaml
from .scanner import Scanner
from .job_spec import JobSpec
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
    Scan the locations for the workflow files
    """
    workflow_files = []
    for loc in locations:
        scanner = Scanner(loc)
        workflow_files.extend(scanner.scan())
    return workflow_files


def specs_from_file(file_path):
    specs = []
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
        jobs = data.get('jobs', {})
        for t, params in jobs.items():
            specs.append(JobSpec.from_dict(t, params))
    return specs


def parse_workflow_files(workflow_files):
    """
    Parse workflow files (ktests.yaml)
    """
    specs = []
    for file in workflow_files:
        specs.extend(specs_from_file(file))
    return specs


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
