from unittest.mock import patch, MagicMock, ANY, mock_open
from types import SimpleNamespace
from pathlib import Path
from kuristo.batch.backend import ScriptParameters
from kuristo.cli._batch import (
    build_actions,
    required_cores,
    create_script_params,
    write_job_metadata,
    read_job_metadata
)


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
    skipped_spec = SimpleNamespace(skip=True, timeout_minutes=0, defaults=None, working_directory=None)
    active_spec = SimpleNamespace(skip=False, timeout_minutes=30, defaults=None, working_directory=None)

    # build_actions returns actions with num_cores
    mock_build_actions.return_value = [SimpleNamespace(num_cores=4)]

    # Act
    params = create_script_params("kuristo-job-1", Path("wf.yaml"), "12", 1, [skipped_spec, active_spec], workdir)

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

    params = create_script_params("kuristo-job-0", Path("wf.yaml"), "12", 0, specs, workdir)

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
        SimpleNamespace(skip=False, timeout_minutes=10, defaults=None, working_directory=None),
        SimpleNamespace(skip=False, timeout_minutes=20, defaults=None, working_directory=None),
    ]
    # First spec -> 2 cores, second -> 8 cores
    mock_build_actions.side_effect = [
        [SimpleNamespace(num_cores=2)],
        [SimpleNamespace(num_cores=8)]
    ]

    params = create_script_params("job-2", Path("wf.yaml"), "12", 2, specs, workdir)

    assert params.n_cores == 8  # max of both
    assert params.max_time == 30  # sum
    assert params.partition == 'normal'


def test_write_metadata():
    job_id = "job-123"
    backend_name = "slurm"
    workdir = Path("/fake/workdir")

    m = mock_open()
    with patch("builtins.open", m), patch("yaml.safe_dump") as mock_safe_dump:
        write_job_metadata(job_id, backend_name, workdir)

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
        read_job_metadata(fake_path)

    m.assert_called_once_with(fake_path, "r")
    mock_safe_load.assert_called_once()
