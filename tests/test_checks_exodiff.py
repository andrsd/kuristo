from unittest.mock import MagicMock, patch

import pytest

from kuristo.actions import ExodiffCheck
from kuristo.context import Context


@pytest.fixture
def dummy_context():
    ctx = MagicMock(spec=Context)
    ctx.env = {}
    ctx.vars = {"steps": {}}
    return ctx


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directory with test files"""
    # Create dummy test files
    (tmp_path / "reference.e").touch()
    (tmp_path / "test.e").touch()

    return tmp_path


# ===== BASIC COMMAND CREATION TESTS =====


def test_create_command_basic(dummy_context, temp_dirs):
    """Test basic command creation with just reference and test files"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        working_dir=str(temp_dirs),
    )
    cmd = check.create_command()
    assert cmd[0] == "exodiff"
    assert len(cmd) == 3  # exodiff + reference + test
    assert any("reference.e" in arg for arg in cmd)
    assert any("test.e" in arg for arg in cmd)


def test_create_command_with_abs_tol(dummy_context, temp_dirs):
    """Test command creation with absolute tolerance"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        working_dir=str(temp_dirs),
        **{"abs-tol": 0.001},
    )
    cmd = check.create_command()
    assert "exodiff" in cmd
    assert "-tolerance" in cmd
    assert "0.001" in cmd
    assert "-absolute" in cmd
    assert any("reference.e" in arg for arg in cmd)
    assert any("test.e" in arg for arg in cmd)


def test_create_command_with_rel_tol(dummy_context, temp_dirs):
    """Test command creation with relative tolerance"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        working_dir=str(temp_dirs),
        **{"rel-tol": 0.01},
    )
    cmd = check.create_command()
    assert "exodiff" in cmd
    assert "-tolerance" in cmd
    assert "0.01" in cmd
    assert "-absolute" in cmd
    assert any("reference.e" in arg for arg in cmd)
    assert any("test.e" in arg for arg in cmd)


def test_create_command_with_floor(dummy_context, temp_dirs):
    """Test command creation with floor parameter"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        working_dir=str(temp_dirs),
        floor=1e-10,
    )
    cmd = check.create_command()
    assert "exodiff" in cmd
    assert "-Floor" in cmd
    assert "1e-10" in cmd
    assert any("reference.e" in arg for arg in cmd)
    assert any("test.e" in arg for arg in cmd)


def test_create_command_with_all_tolerances(dummy_context, temp_dirs):
    """Test command creation with absolute tolerance, relative tolerance, and floor"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        floor=1e-12,
        **{"abs-tol": 0.001, "rel-tol": 0.01},
    )
    cmd = check.create_command()
    assert cmd.count("-tolerance") == 2
    assert cmd.count("-absolute") == 2
    assert "0.001" in cmd
    assert "0.01" in cmd
    assert "-Floor" in cmd
    assert "1e-12" in cmd


def test_create_command_with_extra_args(dummy_context, temp_dirs):
    """Test command creation with extra arguments"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        working_dir=str(temp_dirs),
        extra_args=["--coord-tol", "0.01", "--verbose"],
    )
    cmd = check.create_command()
    assert "exodiff" in cmd
    assert "--coord-tol" in cmd
    assert "0.01" in cmd
    assert "--verbose" in cmd
    assert any("reference.e" in arg for arg in cmd)
    assert any("test.e" in arg for arg in cmd)


def test_create_command_with_all_parameters(dummy_context, temp_dirs):
    """Test command creation with all parameters"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        floor=1e-10,
        extra_args=["--verbose"],
        **{"abs-tol": 0.001, "rel-tol": 0.01},
    )
    cmd = check.create_command()
    assert "exodiff" in cmd
    assert "-tolerance" in cmd
    assert "0.001" in cmd
    assert "0.01" in cmd
    assert "-absolute" in cmd
    assert "-Floor" in cmd
    assert "1e-10" in cmd
    assert "--verbose" in cmd


# ===== PATH RESOLUTION TESTS =====


def test_create_command_with_absolute_paths(dummy_context):
    """Test that absolute paths are used as-is"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="/absolute/path/reference.e",
        test="/absolute/path/test.e",
    )
    cmd = check.create_command()
    assert "/absolute/path/reference.e" in cmd
    assert "/absolute/path/test.e" in cmd


# ===== RUN BEHAVIOR TESTS =====


def test_run_returns_zero_on_success(dummy_context, temp_dirs):
    """Test that run returns 0 when exodiff succeeds"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
    )
    with patch("kuristo.actions.process_action.ProcessAction.run", return_value=0):
        result = check.run()
    assert result == 0


def test_run_returns_exit_code_on_diff_with_fail_on_diff_true(dummy_context, temp_dirs):
    """Test that run returns non-zero exit code when exodiff finds differences and fail_on_diff=True"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        fail_on_diff=True,
    )
    with patch("kuristo.actions.process_action.ProcessAction.run", return_value=2):
        result = check.run()
    assert result == 2


def test_run_returns_zero_on_diff_with_fail_on_diff_false(dummy_context, temp_dirs):
    """Test that run returns 0 when exodiff finds differences but fail_on_diff=False"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        fail_on_diff=False,
    )
    with patch("kuristo.actions.process_action.ProcessAction.run", return_value=2):
        result = check.run()
    assert result == 0


def test_run_returns_zero_on_no_diff(dummy_context, temp_dirs):
    """Test that run returns 0 when there are no differences"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        fail_on_diff=True,
    )
    with patch("kuristo.actions.process_action.ProcessAction.run", return_value=0):
        result = check.run()
    assert result == 0


def test_run_with_various_exit_codes_fail_on_diff_true(dummy_context, temp_dirs):
    """Test various exit codes with fail_on_diff=True"""
    exit_codes = [1, 2, 5, 127]
    for exit_code in exit_codes:
        check = ExodiffCheck(
            name="test",
            context=dummy_context,
            id=None,
            reference="reference.e",
            test="test.e",
            fail_on_diff=True,
        )
        with patch("kuristo.actions.process_action.ProcessAction.run", return_value=exit_code):
            result = check.run()
        assert result == exit_code


def test_run_with_various_exit_codes_fail_on_diff_false(dummy_context, temp_dirs):
    """Test various exit codes with fail_on_diff=False always returns 0"""
    exit_codes = [1, 2, 5, 127]
    for exit_code in exit_codes:
        check = ExodiffCheck(
            name="test",
            context=dummy_context,
            id=None,
            reference="reference.e",
            test="test.e",
            fail_on_diff=False,
        )
        with patch("kuristo.actions.process_action.ProcessAction.run", return_value=exit_code):
            result = check.run()
        assert result == 0


# ===== INITIALIZATION TESTS =====


def test_init_stores_all_parameters(dummy_context, temp_dirs):
    """Test that __init__ properly stores all parameters"""
    check = ExodiffCheck(
        name="test_check",
        context=dummy_context,
        id="step_1",
        reference="reference.e",
        test="test.e",
        floor=1e-10,
        extra_args=["--verbose"],
        fail_on_diff=False,
        **{"abs-tol": 0.001, "rel-tol": 0.01},
    )
    assert check.name == "test_check"
    assert check._abs_tol == 0.001
    assert check._rel_tol == 0.01
    assert check._floor == 1e-10
    assert check._extra_args == ["--verbose"]
    assert check._fail_on_diff is False


def test_init_default_fail_on_diff(dummy_context, temp_dirs):
    """Test that fail_on_diff defaults to True"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
    )
    assert check._fail_on_diff is True


def test_init_default_extra_args(dummy_context, temp_dirs):
    """Test that extra_args defaults to empty list"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
    )
    assert check._extra_args == []


def test_init_default_tolerances(dummy_context, temp_dirs):
    """Test that tolerances default to None"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
    )
    assert check._abs_tol is None
    assert check._rel_tol is None
    assert check._floor is None


# ===== EDGE CASE TESTS =====


def test_empty_extra_args(dummy_context, temp_dirs):
    """Test that empty extra_args list doesn't break command creation"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        extra_args=[],
    )
    cmd = check.create_command()
    assert cmd is not None
    assert len(cmd) == 3


def test_tolerance_zero_is_valid(dummy_context, temp_dirs):
    """Test that tolerance of 0 is valid"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        **{"abs-tol": 0.0},
    )
    cmd = check.create_command()
    assert "0.0" in cmd or "0" in cmd


def test_very_small_tolerance(dummy_context, temp_dirs):
    """Test with very small tolerance values"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        floor=1e-15,
        **{"rel-tol": 1e-12},
    )
    cmd = check.create_command()
    assert "1e-15" in cmd
    assert "1e-12" in cmd


def test_command_with_spaces_in_paths(dummy_context):
    """Test that paths with spaces are handled"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="/path with spaces/reference.e",
        test="/path with spaces/test.e",
    )
    cmd = check.create_command()
    assert "/path with spaces/reference.e" in cmd
    assert "/path with spaces/test.e" in cmd


def test_command_order_is_consistent(dummy_context, temp_dirs):
    """Test that command always puts reference before test"""
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        working_dir=str(temp_dirs),
        **{"abs-tol": 0.001},
    )
    cmd = check.create_command()
    # Find indices of elements containing reference and test
    ref_idx = next(i for i, arg in enumerate(cmd) if "reference.e" in arg)
    test_idx = next(i for i, arg in enumerate(cmd) if "test.e" in arg)
    assert ref_idx < test_idx


def test_multiple_extra_args(dummy_context, temp_dirs):
    """Test with multiple extra arguments"""
    extra_args = ["-coord-tol", "0.01", "-nodal-tol", "0.02", "-elem-tol", "0.03"]
    check = ExodiffCheck(
        name="test",
        context=dummy_context,
        id=None,
        reference="reference.e",
        test="test.e",
        extra_args=extra_args,
    )
    cmd = check.create_command()
    for arg in extra_args:
        assert arg in cmd
