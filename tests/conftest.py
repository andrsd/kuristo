import pytest


@pytest.fixture
def test_workspace(tmp_path):
    """
    Provides a fresh, isolated directory resembling a Kuristo repo.
    Includes an empty `.kuristo/` structure by default.
    """
    workdir = tmp_path / "kuristo-project"
    workdir.mkdir()
    (workdir / ".kuristo").mkdir()
    return workdir


@pytest.fixture
def minimal_workflow_yaml():
    return """
    jobs:
      test:
        description: test
        steps:
          - name: test echo
            run: echo Hello
    """
