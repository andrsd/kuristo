import pytest

from kuristo.config import Config
from kuristo.exceptions import UserException


def test_config_default_missing_ok(tmp_path):
    # If path is None, default is used. Since config_dir / config.yaml won't exist in a temp dir,
    # it should silently succeed and load empty config defaults.
    from unittest.mock import patch

    # Mock find_kuristo_root to return a temp path where config.yaml is missing
    with patch("kuristo.utils.find_kuristo_root", return_value=tmp_path):
        cfg = Config(path=None)
        assert cfg.path == tmp_path / "config.yaml"
        # Should not raise exception, but load default values
        assert cfg.workflow_filename == "kuristo.yaml"


def test_config_custom_missing_raises(tmp_path):
    missing_path = tmp_path / "non_existent_config.yaml"
    with pytest.raises(UserException) as excinfo:
        Config(path=missing_path)
    assert "Configuration file not found" in str(excinfo.value)
    assert str(missing_path) in str(excinfo.value)


def test_config_invalid_yaml_raises(tmp_path):
    bad_config_path = tmp_path / "bad_config.yaml"
    bad_config_path.write_text("""
base:
  console-width: 100
  invalid_yaml: [
""")
    with pytest.raises(UserException) as excinfo:
        Config(path=bad_config_path)
    assert "Configuration YAML syntax error" in str(excinfo.value)
    assert str(bad_config_path) in str(excinfo.value)
    assert "line" in str(excinfo.value).lower()


def test_config_success_loading(tmp_path):
    valid_config_path = tmp_path / "valid_config.yaml"
    valid_config_path.write_text("""
base:
  workflow-filename: "my_custom_workflow.yaml"
  console-width: 120
""")
    cfg = Config(path=valid_config_path)
    assert cfg.workflow_filename == "my_custom_workflow.yaml"
    assert cfg.console_width == 120
