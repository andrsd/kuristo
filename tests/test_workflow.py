import pytest

from kuristo.exceptions import UserException
from kuristo.workflow import workflow_from_file


def test_workflow_from_file_success(tmp_path):
    wf_path = tmp_path / "valid_wf.yaml"
    wf_path.write_text("""
name: My Workflow
jobs:
  test_job:
    description: "A successful job"
    steps:
      - name: "Step 1"
        run: "echo hello"
""")
    wf = workflow_from_file(wf_path)
    assert wf is not None
    assert wf.name == "My Workflow"
    assert "test_job" in wf.jobs
    assert wf.jobs["test_job"].description == "A successful job"


def test_workflow_from_file_not_found(tmp_path):
    missing_path = tmp_path / "does_not_exist.yaml"
    with pytest.raises(UserException) as excinfo:
        workflow_from_file(missing_path)
    assert "Workflow file not found" in str(excinfo.value)
    assert str(missing_path) in str(excinfo.value)


def test_workflow_from_file_invalid_yaml(tmp_path):
    bad_yaml_path = tmp_path / "bad_yaml.yaml"
    # YAML with inconsistent indentation or trailing colon in list is invalid
    bad_yaml_path.write_text("""
jobs:
  test_job:
    steps:
      - name: Step 1
      run: echo hello: unmatched colon
      - [
""")
    with pytest.raises(UserException) as excinfo:
        workflow_from_file(bad_yaml_path)
    assert "YAML syntax error" in str(excinfo.value)
    assert str(bad_yaml_path) in str(excinfo.value)
    # PyYAML's error message should mention line numbers or markers
    assert "line" in str(excinfo.value).lower()


def test_workflow_from_file_schema_validation_error(tmp_path):
    invalid_schema_path = tmp_path / "invalid_schema.yaml"
    # steps must be a list, but we supply a string, which triggers ValidationError
    invalid_schema_path.write_text("""
jobs:
  test_job:
    description: "Invalid because steps is not a list"
    steps: "this should be a list"
""")
    with pytest.raises(UserException) as excinfo:
        workflow_from_file(invalid_schema_path)

    err_str = str(excinfo.value)
    assert "syntax error found in" in err_str
    assert str(invalid_schema_path) in err_str
    assert "steps" in err_str
