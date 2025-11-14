import yaml
import os
import fcntl
import re
from datetime import datetime
from pathlib import Path
import kuristo.config as config
import kuristo.ui as ui
import kuristo.utils as utils
from kuristo.scanner import scan_locations
from kuristo.batch import get_backend
from kuristo.batch.backend import ScriptParameters
from kuristo.scheduler import Scheduler, create_jobs
from kuristo.resources import Resources
from kuristo.job import Job
from kuristo.job_spec import JobSpec, specs_from_file, parse_workflow_files
from kuristo.action_factory import ActionFactory
from kuristo.context import Context
from kuristo.plugin_loader import load_user_steps_from_kuristo_dir
import kuristo.cli._run as cli_run


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


def create_script_params(
    job_name: str,
    workflow_file: Path,
    run_id: str,
    first_job_num: int,
    specs: list[JobSpec],
    workdir: Path
) -> ScriptParameters:
    """
    Create a specification for job submission into a queue

    @param workflow_file Workflow file to run
    @param run_id Kuristo run ID
    @param first_job_num Kuristo job number (i.e. NOT a job ID in the queue)
           we start numbering from
    @param specs `JobSpec`s from a workflow file
    @param workdir Working directory (this is where the job is gonna run)
    @param config Kuristo config
    @return Script parameters
    """
    n_cores = 1
    max_time = 0
    for sp in specs:
        if sp.skip:
            pass
        else:
            context = Context(
                base_env=None,
                working_directory=sp.working_directory,
                defaults=sp.defaults
            )
            actions = build_actions(sp, context)
            n_cores = max(n_cores, required_cores(actions))
            max_time += sp.timeout_minutes

    cfg = config.get()
    return ScriptParameters(
        name=job_name,
        n_cores=n_cores,
        max_time=max_time,
        work_dir=workdir,
        partition=cfg.batch_partition,
        run_id=run_id,
        first_job_num=first_job_num,
        workflow_file=workflow_file
    )


def update_report_atomic(yaml_path: Path, new_results: list):
    """
    Append new results into a yaml file

    @param yaml_path File we want to update
    @param new_results Results to add
    """
    yaml_path = Path(yaml_path)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)

        f.seek(0)
        try:
            report = yaml.safe_load(f) or {"results": []}
            results = report['results']
        except yaml.YAMLError:
            results = []

        results.extend(new_results)

        tmp_path = yaml_path.with_suffix(".tmp")
        cli_run.write_report_yaml(tmp_path, results, 0.)

        os.replace(tmp_path, yaml_path)


def write_job_metadata(batch_job_id, backend_name, workdir):
    # metadata for the job in the queue
    metadata = {
        'id': batch_job_id,
        'backend': backend_name
    }

    metadata_path = Path(workdir) / "metadata.yaml"
    with open(metadata_path, "w") as f:
        yaml.safe_dump({'job': metadata}, f, sort_keys=False)


def read_job_metadata(path: Path):
    metadata = None
    with open(path, "r") as f:
        metadata = yaml.safe_load(f)
    return metadata


def batch_submit(args):
    """
    Submit jobs into HPC queue
    """
    locations = args.locations or ["."]

    cfg = config.get()
    if args.partition is not None:
        cfg.batch_partition = args.partition
    if args.backend is not None:
        cfg.batch_backend = args.backend

    backend = get_backend(cfg.batch_backend)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = utils.create_run_output_dir(cfg.log_dir, sub_dir=run_id)
    utils.prune_old_runs(cfg.log_dir, cfg.log_history)
    utils.update_latest_symlink(cfg.log_dir, out_dir)
    load_user_steps_from_kuristo_dir()

    n_jobs = 0
    job_num = 0
    workflow_files = scan_locations(locations)
    for f in workflow_files:
        n_jobs += 1
        workdir = out_dir / f"job-{n_jobs}"
        workdir.mkdir()

        specs = specs_from_file(f)
        job_name = f"kuristo-job-{n_jobs}"
        s = create_script_params(job_name, f, run_id, job_num, specs, workdir)

        batch_job_id = backend.submit(s)
        write_job_metadata(batch_job_id, backend.name, workdir)

        for sp in specs:
            jobs = create_jobs(sp, out_dir)
            job_num += len(jobs)

    ui.console().print(f'Submitted {n_jobs} jobs')


def batch_status(args):
    """
    Get job status in queue
    """
    cfg = config.get()
    jobs_dir = cfg.log_dir / "runs" / "latest"

    job_dir_pattern = re.compile(r"job-\d+")
    metadata = []
    for entry in os.listdir(jobs_dir):
        path = os.path.join(jobs_dir, entry)
        if os.path.isdir(path) and job_dir_pattern.fullmatch(entry):
            metadata_path = os.path.join(path, "metadata.yaml")
            if os.path.isfile(metadata_path):
                metadata.append(read_job_metadata(Path(metadata_path)))

    for m in metadata:
        batch_job_id = str(m["job"]["id"])
        backend = get_backend(m["job"]["backend"])
        status = backend.status(batch_job_id)
        ui.console().print(f'[{batch_job_id}] {status}')


def batch_run(args):
    """
    Run a workflow
    """
    Job.ID = args.first_job_id

    cfg = config.get()
    out_dir = utils.create_run_output_dir(cfg.log_dir, args.run_id)
    utils.update_latest_symlink(cfg.log_dir, out_dir)

    load_user_steps_from_kuristo_dir()

    specs = parse_workflow_files([args.workflow_file])
    rcs = Resources()
    scheduler = Scheduler(specs, rcs, out_dir)
    scheduler.check()
    scheduler.run_all_jobs()

    results = cli_run.create_results(scheduler.jobs)
    yaml_path = out_dir / "report.yaml"

    update_report_atomic(yaml_path, results)

    return scheduler.exit_code()


def batch(args):
    if args.batch_command == "submit":
        batch_submit(args)
    elif args.batch_command == "status":
        batch_status(args)
    elif args.batch_command == "run":
        batch_run(args)
