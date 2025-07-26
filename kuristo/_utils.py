import sys
import subprocess
import os
import shutil
import re
import yaml
from jinja2 import Template
from datetime import datetime
from pathlib import Path


RUN_DIR_PATTERN = re.compile(r"\d{8}_\d{6}")


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


def create_run_output_dir(base_log_dir: Path) -> Path:
    runs_dir = base_log_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = runs_dir / timestamp
    run_dir.mkdir()
    return run_dir


def prune_old_runs(log_dir: Path, keep_last_n: int):
    runs_dir = log_dir / "runs"
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and RUN_DIR_PATTERN.match(d.name)]
    run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    for old_run in run_dirs[keep_last_n:]:
        shutil.rmtree(old_run)


def update_latest_symlink(log_dir: Path, latest_run_dir: Path):
    """
    Create or update a symlink named 'latest' inside base_log_dir that points to latest_run_dir.
    """
    runs_dir = log_dir / "runs"
    latest_link = runs_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    relative_target = latest_run_dir.relative_to(runs_dir)
    latest_link.symlink_to(relative_target, target_is_directory=True)


def rich_job_name(job_name):
    return job_name.replace("[", "\\[")


def interpolate_str(text: str, variables: dict) -> str:
    normalized = text.replace("${{", "{{").replace("}}", "}}")
    template = Template(normalized)
    return template.render(**variables)


def minutes_to_hhmmss(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    seconds = 0
    return f"{hours:0d}:{mins:02d}:{seconds:02d}"


def human_time(elapsed_time: float) -> str:
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes:
        parts.append(f"{int(minutes)}m")
    parts.append(f"{seconds:.2f}s")

    return " ".join(parts)


def human_time2(elapsed_time) -> str:
    """
    PLEASE, give me a BETTER name
    """
    if isinstance(elapsed_time, float):
        return f"{elapsed_time:.2f}s"
    else:
        return ""


def read_report(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)
