import pytest
from unittest.mock import MagicMock, patch
from kuristo.context import Context
from kuristo.actions import H5DiffCheck


@pytest.fixture
def dummy_context():
    ctx = MagicMock(spec=Context)
    ctx.env = {}
    ctx.vars = {"steps": {}}
    return ctx


# ===== BACKWARD COMPATIBILITY TESTS (Single file comparison) =====


def test_create_command_with_abs_tol(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{"abs-tol": 0.001},
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
        **{"rel-tol": 0.01},
    )
    cmd = check.create_command()
    assert "--relative=0.01" in cmd
    assert "gold.h5" in cmd
    assert "test.h5" in cmd


def test_missing_tolerances_raises(dummy_context):
    with pytest.raises(RuntimeError, match="Must provide either `rel-tol` or `abs-tol`"):
        H5DiffCheck(name="test", context=dummy_context, gold="gold.h5", test="test.h5")


def test_run_returns_exit_code_on_diff(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{"abs-tol": 0.001, "fail-on-diff": True},
    )
    check.run_command = MagicMock(return_value=2)
    assert check.run() == 2


def test_run_allows_diff_when_flag_false(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{"abs-tol": 0.001, "fail-on-diff": False},
    )
    check.run_command = MagicMock(return_value=2)
    assert check.run() == 0


def test_run_success(dummy_context):
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        **{"abs-tol": 0.001},
    )
    check.run_command = MagicMock(return_value=0)
    assert check


# ===== MULTIPLE DATASETS TESTS =====


def test_datasets_requires_path(dummy_context):
    """Dataset must have 'path' field"""
    with pytest.raises(RuntimeError, match="must have a 'path' field"):
        H5DiffCheck(
            name="test",
            context=dummy_context,
            gold="gold.h5",
            test="test.h5",
            datasets=[
                {"rel-tol": 1e-6}  # missing 'path'
            ],
        )


def test_datasets_requires_tolerance(dummy_context):
    """Each dataset must have rel-tol or abs-tol"""
    with pytest.raises(RuntimeError, match="must provide either `rel-tol` or `abs-tol`"):
        H5DiffCheck(
            name="test",
            context=dummy_context,
            gold="gold.h5",
            test="test.h5",
            datasets=[
                {"path": "/pressure"}  # missing tolerance
            ],
        )


def test_create_command_for_dataset(dummy_context):
    """Test command creation for individual dataset"""
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        datasets=[{"path": "/pressure", "rel-tol": 1e-6}],
    )
    cmd = check._create_command_for_dataset({"path": "/pressure", "rel-tol": 1e-6})
    assert "h5diff" in cmd
    assert "--relative=1e-06" in cmd
    assert "/pressure" in cmd
    assert "gold.h5" in cmd
    assert "test.h5" in cmd


def test_multiple_datasets_all_pass(dummy_context):
    """All dataset comparisons pass"""
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        datasets=[
            {"path": "/pressure", "rel-tol": 1e-6},
            {"path": "/velocity", "abs-tol": 0.001},
            {"path": "/temperature", "rel-tol": 1e-5},
        ],
    )

    mock_popen = MagicMock()
    mock_popen.communicate.return_value = (b"No differences found", None)
    mock_popen.returncode = 0

    with patch("subprocess.Popen", return_value=mock_popen):
        assert check.run() == 0


def test_multiple_datasets_one_fails(dummy_context):
    """One dataset comparison fails, should fail overall"""
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        datasets=[
            {"path": "/pressure", "rel-tol": 1e-6},
            {"path": "/velocity", "abs-tol": 0.001},
        ],
        **{"fail-on-diff": True},
    )

    # First call succeeds, second fails
    mock_popen = MagicMock()
    mock_popen.communicate.return_value = (b"", None)
    mock_popen.returncode = 1

    with patch("subprocess.Popen", return_value=mock_popen):
        assert check.run() == 1


def test_multiple_datasets_fail_on_diff_false(dummy_context):
    """Multiple datasets fail but fail-on-diff is false"""
    check = H5DiffCheck(
        name="test",
        context=dummy_context,
        gold="gold.h5",
        test="test.h5",
        datasets=[{"path": "/pressure", "rel-tol": 1e-6}],
        **{"fail-on-diff": False},
    )

    mock_popen = MagicMock()
    mock_popen.communicate.return_value = (b"Differences found", None)
    mock_popen.returncode = 1

    with patch("subprocess.Popen", return_value=mock_popen):
        assert check.run() == 0


def test_datasets_must_be_list(dummy_context):
    """datasets parameter must be a list"""
    with pytest.raises(RuntimeError, match="`datasets` must be a list"):
        H5DiffCheck(
            name="test",
            context=dummy_context,
            gold="gold.h5",
            test="test.h5",
            datasets={"path": "/pressure", "rel-tol": 1e-6},  # not a list
        )
