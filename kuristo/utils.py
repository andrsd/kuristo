import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Template

RUN_DIR_PATTERN = re.compile(r"\d{8}-\d{6}")


def find_kuristo_root(start_path=None):
    """
    Search up from start_path (or cwd) to find the first directory containing `.kuristo/`
    """
    current = Path(start_path or Path.cwd()).resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".kuristo").is_dir():
            return parent / ".kuristo"

    return None


def get_default_core_limit():
    if sys.platform == "darwin":
        try:
            # Apple Silicon: performance cores
            output = subprocess.check_output(
                ["sysctl", "-n", "hw.perflevel0.physicalcpu"], text=True
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


def create_run_output_dir(base_log_dir: Path, sub_dir=None) -> Path:
    """
    Create a directory for log files

    @param base_log_dir Base directory that stores the information with runs, i.e. `.kuristo-out`
    @param sub_dir Optional parameter that can specify the sub-directory name. If `None` date time stamp is used.
    """
    runs_dir = base_log_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    if sub_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    elif RUN_DIR_PATTERN.match(sub_dir):
        timestamp = sub_dir
    else:
        raise RuntimeError("run-id must have the YYYYmmDD-HHMMSS pattern")
    run_dir = runs_dir / timestamp
    run_dir.mkdir(exist_ok=True)
    return run_dir


def prune_old_runs(log_dir: Path, keep_last_n: int):
    runs_dir = log_dir / "runs"
    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and RUN_DIR_PATTERN.match(d.name)]
    run_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    for old_run in run_dirs[keep_last_n:]:
        # Skip deletion if run is tagged
        if is_run_tagged(log_dir, old_run.name):
            continue
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


TAG_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def validate_tag_name(tag_name: str) -> bool:
    """Validate tag name against allowed pattern"""
    return TAG_NAME_PATTERN.match(tag_name) is not None


def create_tag(log_dir: Path, tag_name: str, run_id: str):
    """Create a tag (symlink) pointing to a run directory"""
    if not validate_tag_name(tag_name):
        raise RuntimeError(
            f"Invalid tag name '{tag_name}'. Must contain only letters, numbers, dots, hyphens, and underscores."
        )

    runs_dir = log_dir / "runs"
    tags_dir = log_dir / "tags"
    tags_dir.mkdir(exist_ok=True)

    # Verify run exists
    run_dir = runs_dir / run_id
    if not run_dir.exists():
        raise RuntimeError(f"Run '{run_id}' does not exist")

    # Create or update tag
    tag_path = tags_dir / tag_name
    if tag_path.exists() or tag_path.is_symlink():
        tag_path.unlink()

    relative_target = Path("..") / "runs" / run_id
    tag_path.symlink_to(relative_target, target_is_directory=True)


def delete_tag(log_dir: Path, tag_name: str):
    """Delete a tag (symlink only, not the run)"""
    tags_dir = log_dir / "tags"
    tag_path = tags_dir / tag_name

    if not tag_path.exists() and not tag_path.is_symlink():
        raise RuntimeError(f"Tag '{tag_name}' does not exist")

    tag_path.unlink()


def list_tags(log_dir: Path) -> list:
    """List all tags and their target run IDs. Returns [(tag_name, run_id), ...]"""
    tags_dir = log_dir / "tags"
    if not tags_dir.exists():
        return []

    tags = []
    for tag_path in tags_dir.iterdir():
        if tag_path.is_symlink():
            try:
                target = tag_path.resolve()
                run_id = target.name
                tags.append((tag_path.name, run_id))
            except Exception:
                # Broken symlink, skip
                pass

    tags.sort(key=lambda x: x[0])  # Sort by tag name
    return tags


def get_tags_for_run(log_dir: Path, run_id: str) -> list:
    """Get all tag names pointing to a specific run"""
    all_tags = list_tags(log_dir)
    return [tag_name for tag_name, target_run_id in all_tags if target_run_id == run_id]


def is_run_tagged(log_dir: Path, run_id: str) -> bool:
    """Check if a run has any tags"""
    return len(get_tags_for_run(log_dir, run_id)) > 0


def resolve_run_id(log_dir: Path, run_id: str) -> str:
    """
    Resolve a run ID (which may be an alias like a tag) to the actual run ID.
    If run_id is a tag, follows the symlink to get the actual run ID.
    Otherwise returns run_id unchanged.
    """
    tags_dir = log_dir / "tags"
    tag_path = tags_dir / run_id

    # Check if it's a tag
    if tag_path.is_symlink():
        try:
            target = tag_path.resolve()
            return target.name
        except Exception:
            # If symlink is broken, return the original input
            return run_id

    # Not a tag, return as-is
    return run_id


def interpolate_str(text: str, variables: dict) -> str:
    normalized = text.replace("${{", "{{")
    template = Template(normalized)
    return template.render(**variables)


def minutes_to_hhmmss(minutes: int) -> str:
    """
    Convert minutes into "H:MM:SS"

    @param minutes Number of minutes to convert
    @return String formatted as "H:MM:SS"
    """
    hours = minutes // 60
    mins = minutes % 60
    seconds = 0
    return f"{hours:0d}:{mins:02d}:{seconds:02d}"


def human_time(seconds: float) -> str:
    """
    Convert time to human form

    @param seconds Number of seconds
    @return <H>h <M>m <S>s
    """
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if hours:
        parts.append(f"{int(hours)}h")
    if minutes:
        parts.append(f"{int(minutes)}m")
    parts.append(f"{seconds:.2f}s")

    return " ".join(parts)


def read_report(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_filters(args):
    filters = []
    if args.failed:
        filters.append("failed")
    if args.skipped:
        filters.append("skipped")
    if args.passed:
        filters.append("success")
    return filters


def scalar_or_list(kwargs: dict, name: str):
    """
    Look at kwargs for "parameter" `name` and return it either as a `float` or
    a list of `float`s.
    """
    if kwargs[name] is None:
        raise ValueError(f"{name} is required")
    if isinstance(kwargs[name], (list, tuple)):
        return [float(x) for x in kwargs[name]]
    else:
        return float(kwargs[name])


def filter_specs_by_labels(specs, requested_labels):
    """
    Filter job specs by labels using OR logic.

    Args:
        specs: List of JobSpec objects
        requested_labels: List of label strings to filter by

    Returns:
        Tuple of (filtered_specs, total_count, filtered_count)
    """
    if not requested_labels:
        return specs, len(specs), len(specs)

    filtered = []
    for spec in specs:
        if spec.labels and any(label in spec.labels for label in requested_labels):
            filtered.append(spec)

    return filtered, len(specs), len(filtered)
