from unittest.mock import patch, MagicMock
from kuristo.actions.mpi_action import MPIAction
from kuristo.context import Context


class DummyMPIAction(MPIAction):
    def create_sub_command(self) -> str:
        return "my_mpi_program"


def make_context():
    ctx = MagicMock(spec=Context)
    ctx.vars = {}
    return ctx


def test_default_num_cores():
    ctx = make_context()
    action = DummyMPIAction(name="mpi_test", context=ctx)
    assert action.num_cores == 1  # default


def test_custom_num_cores():
    ctx = make_context()
    action = DummyMPIAction(name="mpi_test", context=ctx, **{'num-procs': 8})
    assert action.num_cores == 8


@patch("kuristo.actions.mpi_action.config.get")
def test_create_command_uses_config_and_sub_command(mock_get):
    ctx = make_context()
    mock_get.return_value = MagicMock(mpi_launcher="mpirun")
    action = DummyMPIAction(name="mpi_test", context=ctx, **{'num-procs': 4})

    result = action.create_command()

    assert result == "mpirun -np 4 my_mpi_program"
    mock_get.assert_called_once()
