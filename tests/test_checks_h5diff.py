import pytest
from unittest.mock import MagicMock
from kuristo.context import Context
from kuristo.actions import H5DiffCheck


@pytest.fixture
def dummy_context():
    ctx = MagicMock(spec=Context)
    ctx.env = {}
    ctx.vars = {}
    return ctx


def test_create_command_with_abs_tol(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{"abs-tol": 0.001}
    )
    cmd = check.create_command()
    assert "--delta=0.001" in cmd
    assert "gold.h5" in cmd
    assert "test.h5" in cmd


def test_create_command_with_rel_tol(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{"rel-tol": 0.01}
    )
    cmd = check.create_command()
    assert "--relative=0.01" in cmd
    assert "gold.h5" in cmd
    assert "test.h5" in cmd


def test_missing_tolerances_raises(dummy_context):
    with pytest.raises(RuntimeError, match="Must provide either `rel-tol` or `abs-tol`"):
        H5DiffCheck(
            name="test",
            context=dummy_context,
            gold="gold.h5",
            test="test.h5"
        )


def test_run_returns_exit_code_on_diff(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{
            "abs-tol": 0.001,
            "fail-on-diff": True
        }
    )
    check.run_command = MagicMock(return_value=2)
    assert check.run() == 2


def test_run_allows_diff_when_flag_false(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{
            "abs-tol": 0.001,
            "fail-on-diff": False
        }
    )
    check.run_command = MagicMock(return_value=2)
    assert check.run() == 0


def test_run_success(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{
            "abs-tol": 0.001
        }
    )
    check.run_command = MagicMock(return_value=0)
    assert check
