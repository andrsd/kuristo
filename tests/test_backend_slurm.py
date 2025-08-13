import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from kuristo.batch.slurm import SlurmBackend, ScriptParameters


class TestSlurmBackend(unittest.TestCase):

    def setUp(self):
        self.backend = SlurmBackend()
        self.params = ScriptParameters(
            run_id="1",
            first_job_num=1,
            workflow_file=Path("ktests.yaml"),
            name="test_job",
            work_dir=Path("test_dir"),
            n_cores=4,
            max_time=30  # in minutes
        )
        Path("test_dir").mkdir(exist_ok=True)

    @patch("subprocess.run")
    def test_submit_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Submitted batch job 123456"
        )

        job_id = self.backend.submit(self.params)
        self.assertEqual(job_id, "123456")

        script_path = Path("test_dir/slurm_job.sh")
        self.assertTrue(script_path.exists())

    @patch("subprocess.run")
    def test_submit_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Something went wrong"
        )

        with self.assertRaises(RuntimeError) as ctx:
            self.backend.submit(self.params)

        self.assertIn("sbatch failed", str(ctx.exception))

    @patch("subprocess.run")
    def test_status_running(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="RUNNING\n"
        )
        status = self.backend.status("123456")
        self.assertEqual(status, "RUNNING")

    @patch("subprocess.run")
    def test_status_completed_empty_output(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=""
        )
        status = self.backend.status("123456")
        self.assertEqual(status, "COMPLETED")

    @patch("subprocess.run")
    def test_status_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1
        )
        status = self.backend.status("123456")
        self.assertEqual(status, "UNKNOWN")

    def tearDown(self):
        for file in Path("test_dir").glob("*"):
            file.unlink()
        Path("test_dir").rmdir()
