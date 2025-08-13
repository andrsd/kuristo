import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from importlib.resources import files
from kuristo.batch.backend import BatchBackend, ScriptParameters
from kuristo.utils import minutes_to_hhmmss


class SlurmBackend(BatchBackend):

    def __init__(self):
        super().__init__(name="slurm")
        template_dir = files("kuristo").joinpath("templates")
        self._env = Environment(loader=FileSystemLoader(str(template_dir)))

    def submit(self, params: ScriptParameters) -> str:
        script = self._render_job_script(params)
        script_path = Path(params.work_dir) / "slurm_job.sh"
        script_path.write_text(script)

        result = subprocess.run(["sbatch", str(script_path)], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"sbatch failed: {result.stderr.strip()}")

        # Parse SLURM job ID from output like "Submitted batch job 123456"
        job_id = result.stdout.strip().split()[-1]
        return str(job_id)

    def status(self, job_id: str) -> str:
        result = subprocess.run(["squeue", "-j", job_id, "-h", "-o", "%T"], capture_output=True, text=True)
        if result.returncode != 0:
            return "UNKNOWN"
        state = result.stdout.strip()
        return state or "COMPLETED"

    def _render_job_script(self, params: ScriptParameters):
        template = self._env.get_template("slurm_job.sh.j2")
        job = {
            'name': params.name,
            'workdir': params.work_dir,
            'num_tasks': params.n_cores,
            'walltime': minutes_to_hhmmss(params.max_time),
            'partition': params.partition,
            'workflow_file': params.workflow_file.resolve(),
            'run_id': params.run_id,
            'first_job_num': params.first_job_num
        }
        return template.render({"job": job})
