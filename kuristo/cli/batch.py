import yaml
import os
import re
from pathlib import Path
from rich.console import Console
from kuristo.config import Config
from kuristo.scanner import scan_locations
from kuristo.batch import get_backend
from kuristo.batch.backend import ScriptParameters
from kuristo.job_spec import specs_from_file
from kuristo.action_factory import ActionFactory
from kuristo.context import Context
from kuristo._utils import create_run_output_dir, prune_old_runs, update_latest_symlink
from kuristo._plugin_loader import load_user_steps_from_kuristo_dir


def build_actions(spec, context):
    steps = []
    for step in spec.steps:
        action = ActionFactory.create(step, context)
        if action is not None:
            steps.append(action)
    return steps


def required_cores(actions):
    n_cores = 1
    for a in actions:
        n_cores = max(n_cores, a.num_cores)
    return n_cores


def create_script_params(job_num: int, specs, workdir: Path, config: Config):
    """
    Create a specification for job submission into a queue

    @param job_num Kuristo job number (i.e. NOT a job ID in the queue)
    @param specs `JobSpec`s from a workflow file
    @param workdir Working directory (this is where the job is gonna run)
    @param config Kuristo config
    """

    job_name = f"kuristo-job-{job_num}"

    n_cores = 1
    max_time = 0
    for sp in specs:
        if sp.skip:
            pass
        else:
            context = Context(
                config=config,
                base_env=None,
                # matrix=matrix
            )

            actions = build_actions(sp, context)
            n_cores = max(n_cores, required_cores(actions))
            max_time += sp.timeout_minutes

    return ScriptParameters(
        name=job_name,
        n_cores=n_cores,
        max_time=max_time,
        work_dir=workdir,
        partition=config.batch_partition
    )


def write_metadata(job_id, backend_name, workdir):
    # metadata for the job in the queue
    metadata = {
        'id': job_id,
        'backend': backend_name
    }

    metadata_path = Path(workdir) / "metadata.yaml"
    with open(metadata_path, "w") as f:
        yaml.safe_dump({'job': metadata}, f, sort_keys=False)


def read_metadata(path: Path):
    metadata = None
    with open(path, "r") as f:
        metadata = yaml.safe_load(f)
    return metadata


def load_metadata(dir: Path):
    job_dir_pattern = re.compile(r"job-\d+")
    metadata = []
    for entry in os.listdir(dir):
        path = os.path.join(dir, entry)
        if os.path.isdir(path) and job_dir_pattern.fullmatch(entry):
            metadata_path = os.path.join(path, "metadata.yaml")
            if os.path.isfile(metadata_path):
                metadata.append(read_metadata(Path(metadata_path)))
    return metadata


def batch_submit(args):
    """
    Submit jobs into HPC queue
    """
    console = Console(force_terminal=not args.no_ansi, no_color=args.no_ansi, markup=not args.no_ansi)

    try:
        config = Config()
        if args.partition is not None:
            config.batch_partition = args.partition
        if args.backend is not None:
            config.batch_backend = args.backend

        backend = get_backend(config.batch_backend)
        locations = args.location or ["."]
        out_dir = create_run_output_dir(config.log_dir)
        prune_old_runs(config.log_dir, config.log_history)
        update_latest_symlink(config.log_dir, out_dir)
        load_user_steps_from_kuristo_dir()

        job_num = 0
        workflow_files = scan_locations(locations)
        for f in workflow_files:
            job_num += 1
            workdir = out_dir / f"job-{job_num}"
            workdir.mkdir()

            specs = specs_from_file(f)
            s = create_script_params(job_num, specs, workdir, config)

            job_id = backend.submit(s)
            write_metadata(job_id, backend.name, workdir)

        console.print(f'Submitted {job_num} jobs')
    except Exception as e:
        print(e)


def batch_status(args):
    """
    Get job status in queue
    """
    console = Console(force_terminal=not args.no_ansi, no_color=args.no_ansi, markup=not args.no_ansi)
    config = Config()
    jobs_dir = config.log_dir / "runs" / "latest"

    try:
        metadata = load_metadata(jobs_dir)
        for m in metadata:
            job_id = str(m["job"]["id"])
            backend = get_backend(m["job"]["backend"])
            status = backend.status(job_id)
            console.print(f'[{job_id}] {status}')
    except Exception as e:
        print(e)


def batch(args):
    if args.batch_command == "submit":
        batch_submit(args)
    elif args.batch_command == "status":
        batch_status(args)
