from unittest.mock import patch, MagicMock, ANY, mock_open
from types import SimpleNamespace
from pathlib import Path
from kuristo.batch.backend import ScriptParameters
from kuristo.cli._batch import (
    batch_submit,
    batch_status,
    build_actions,
    required_cores,
    create_script_params,
    write_metadata,
    read_metadata,
    load_metadata,
)


@patch("kuristo.cli._batch.write_metadata")
@patch("kuristo.cli._batch.create_script_params")
@patch("kuristo.cli._batch.specs_from_file")
@patch("kuristo.cli._batch.scan_locations")
@patch("kuristo.cli._batch.load_user_steps_from_kuristo_dir")
@patch("kuristo.cli._batch.update_latest_symlink")
@patch("kuristo.cli._batch.prune_old_runs")
@patch("kuristo.cli._batch.create_run_output_dir")
@patch("kuristo.cli._batch.get_backend")
@patch("kuristo.cli._batch.config.get")
def test_batch_submit_basic(
    mock_config_get,
    mock_get_backend,
    mock_create_run_output_dir,
    mock_prune_old_runs,
    mock_update_symlink,
    mock_load_user_steps,
    mock_scan_locations,
    mock_specs_from_file,
    mock_create_script_params,
    mock_write_metadata,
    tmp_path
):
    # Arrange: mock CLI args
    args = SimpleNamespace(
        backend="slurm",
        location=["some/path"],
        no_ansi=True,
        partition='normal'
    )

    # Return value of Config()
    mock_config_instance = MagicMock()
    mock_config_instance.log_dir = Path("/fake/log")
    mock_config_get.return_value = mock_config_instance

    # Mock backend
    mock_backend = MagicMock()
    mock_backend.name = "slurm"
    mock_backend.submit.side_effect = lambda s: f"job-{s.name}"
    mock_get_backend.return_value = mock_backend

    # Mock output dir and workflow files
    out_dir = Path(tmp_path)
    mock_create_run_output_dir.return_value = out_dir
    mock_scan_locations.return_value = [Path("workflow1.yml"), Path("workflow2.yml")]
    mock_specs_from_file.side_effect = lambda path: {"dummy": "spec"}

    # Mock script param creation
    mock_create_script_params.side_effect = lambda num, spec, wd, cfg: ScriptParameters(
        name=f"job{num}",
        work_dir=wd,
        n_cores=4,
        max_time=120,
    )

    # Act
    batch_submit(args)

    # Assert
    assert mock_backend.submit.call_count == 2
    assert mock_write_metadata.call_count == 2
    mock_get_backend.assert_called_once_with("slurm")
    mock_scan_locations.assert_called_once_with(["some/path"])
    mock_specs_from_file.assert_any_call(Path("workflow1.yml"))
    mock_specs_from_file.assert_any_call(Path("workflow2.yml"))


@patch("rich.console.Console.print")
@patch("kuristo.cli._batch.get_backend")
@patch("kuristo.cli._batch.load_metadata")
@patch("kuristo.cli._batch.config.get")
def test_batch_status_basic(mock_config_get, mock_load_metadata, mock_get_backend, mock_console_print):
    # Fake CLI args
    args = SimpleNamespace(no_ansi=True)

    # Return value of Config()
    mock_config_instance = MagicMock()
    mock_config_instance.log_dir = Path("/fake/log")
    mock_config_get.return_value = mock_config_instance

    # Fake metadata from a previous submission
    mock_load_metadata.return_value = [
        {"job": {"id": 1234, "backend": "slurm"}},
        {"job": {"id": 5678, "backend": "slurm"}},
    ]

    # Fake backend with mock status method
    mock_backend = MagicMock()
    mock_backend.status.side_effect = ["RUNNING", "COMPLETED"]
    mock_get_backend.return_value = mock_backend

    batch_status(args)

    # Assert
    mock_load_metadata.assert_called_once_with(Path("/fake/log/runs/latest"))
    assert mock_backend.status.call_count == 2
    mock_backend.status.assert_any_call("1234")
    mock_backend.status.assert_any_call("5678")

    mock_console_print.assert_any_call("[1234] RUNNING")
    mock_console_print.assert_any_call("[5678] COMPLETED")


@patch("kuristo.cli._batch.ActionFactory.create")
def test_build_actions_filters_none(mock_create):
    # Arrange
    step1 = MagicMock(name="Step1")
    step2 = MagicMock(name="Step2")
    step3 = MagicMock(name="Step3")

    # simulate create() returning None for step2
    mock_create.side_effect = ["action1", None, "action3"]

    spec = SimpleNamespace(steps=[step1, step2, step3])
    context = MagicMock()

    # Act
    actions = build_actions(spec, context)

    # Assert
    assert actions == ["action1", "action3"]
    assert mock_create.call_count == 3
    mock_create.assert_any_call(step1, context)
    mock_create.assert_any_call(step2, context)
    mock_create.assert_any_call(step3, context)


def test_required_cores_empty():
    assert required_cores([]) == 1


def test_required_cores_single_action():
    action = SimpleNamespace(num_cores=4)
    assert required_cores([action]) == 4


def test_required_cores_multiple_actions():
    actions = [
        SimpleNamespace(num_cores=2),
        SimpleNamespace(num_cores=8),
        SimpleNamespace(num_cores=4),
    ]
    assert required_cores(actions) == 8


def test_required_cores_all_below_default():
    actions = [
        SimpleNamespace(num_cores=0),
        SimpleNamespace(num_cores=1),
    ]
    assert required_cores(actions) == 1


@patch("kuristo.cli._batch.build_actions")
@patch("kuristo.cli._batch.config.get")
def test_create_script_params_basic(mock_config_get, mock_build_actions):
    # Arrange
    workdir = Path("/fake/workdir")

    # Return value of Config()
    mock_config_instance = MagicMock()
    mock_config_instance.batch_partition = 'normal'
    mock_config_get.return_value = mock_config_instance

    # 2 specs: one skipped, one active
    skipped_spec = SimpleNamespace(skip=True, timeout_minutes=0)
    active_spec = SimpleNamespace(skip=False, timeout_minutes=30)

    # build_actions returns actions with num_cores
    mock_build_actions.return_value = [SimpleNamespace(num_cores=4)]

    # Act
    params = create_script_params(1, [skipped_spec, active_spec], workdir)

    # Assert
    assert isinstance(params, ScriptParameters)
    assert params.name == "kuristo-job-1"
    assert params.work_dir == workdir
    assert params.n_cores == 4
    assert params.max_time == 30
    assert params.partition == 'normal'
    mock_build_actions.assert_called_once_with(active_spec, ANY)


@patch("kuristo.cli._batch.build_actions")
@patch("kuristo.cli._batch.config.get")
def test_create_script_params_all_skipped(mock_config_get, mock_build_actions):
    # Return value of Config()
    mock_config_instance = MagicMock()
    mock_config_instance.batch_partition = 'normal'
    mock_config_get.return_value = mock_config_instance

    workdir = Path("/workdir")
    specs = [SimpleNamespace(skip=True, timeout_minutes=15) for _ in range(3)]

    params = create_script_params(0, specs, workdir)

    assert params.name == "kuristo-job-0"
    assert params.n_cores == 1  # default
    assert params.max_time == 0
    assert params.work_dir == workdir
    assert params.partition == 'normal'
    mock_build_actions.assert_not_called()


@patch("kuristo.cli._batch.build_actions")
@patch("kuristo.cli._batch.config.get")
def test_create_script_params_accumulates_time_and_max_cores(mock_config_get, mock_build_actions):
    # Return value of Config()
    mock_config_instance = MagicMock()
    mock_config_instance.batch_partition = 'normal'
    mock_config_get.return_value = mock_config_instance

    workdir = Path("/data")
    specs = [
        SimpleNamespace(skip=False, timeout_minutes=10),
        SimpleNamespace(skip=False, timeout_minutes=20),
    ]
    # First spec -> 2 cores, second -> 8 cores
    mock_build_actions.side_effect = [
        [SimpleNamespace(num_cores=2)],
        [SimpleNamespace(num_cores=8)]
    ]

    params = create_script_params(2, specs, workdir)

    assert params.n_cores == 8  # max of both
    assert params.max_time == 30  # sum
    assert params.partition == 'normal'


def test_write_metadata():
    job_id = "job-123"
    backend_name = "slurm"
    workdir = Path("/fake/workdir")

    m = mock_open()
    with patch("builtins.open", m), patch("yaml.safe_dump") as mock_safe_dump:
        write_metadata(job_id, backend_name, workdir)

    expected_metadata = {'job': {'id': job_id, 'backend': backend_name}}
    mock_safe_dump.assert_called_once_with(expected_metadata, m(), sort_keys=False)

    # The *first* call to open() should be with the file path and mode "w"
    first_call = m.mock_calls[0]
    assert first_call[0] == ""  # This means the call itself (not __enter__ etc)
    args, _ = first_call[1], first_call[2]
    assert args[0] == workdir / "metadata.yaml"
    assert args[1] == "w"


def test_read_metadata():
    fake_path = Path("/fake/path/metadata.yaml")
    fake_file_content = "some yaml content"

    m = mock_open(read_data=fake_file_content)
    with patch("builtins.open", m), patch("yaml.safe_load") as mock_safe_load:
        read_metadata(fake_path)

    m.assert_called_once_with(fake_path, "r")
    mock_safe_load.assert_called_once()


@patch("kuristo.cli._batch.read_metadata")
@patch("os.listdir")
@patch("os.path.isdir")
@patch("os.path.isfile")
def test_load_metadata(mock_isfile, mock_isdir, mock_listdir, mock_read_metadata):
    base_dir = Path("/fake/logs")

    # Simulate directory entries
    mock_listdir.return_value = ["job-1", "job-2", "not_a_job"]

    # job-1 and job-2 are directories, not_a_job is not
    mock_isdir.side_effect = lambda path: path.endswith("job-1") or path.endswith("job-2")

    # metadata.yaml exists only in job-1, not in job-2
    def isfile_side_effect(path):
        return path.endswith("job-1/metadata.yaml")
    mock_isfile.side_effect = isfile_side_effect

    # read_metadata returns dummy metadata for job-1 only
    mock_read_metadata.return_value = {"job": {"id": "job-1", "backend": "slurm"}}

    result = load_metadata(base_dir)

    mock_listdir.assert_called_once_with(base_dir)
    assert mock_read_metadata.call_count == 1
    mock_read_metadata.assert_called_with(Path("/fake/logs/job-1/metadata.yaml"))
    assert result == [mock_read_metadata.return_value]
