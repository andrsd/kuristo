import pytest
from unittest.mock import patch, MagicMock
from kuristo.resources import Resources


@pytest.fixture
def mock_config():
    cfg = MagicMock()
    cfg.num_cores = 8
    with patch("kuristo.resources.config.get", return_value=cfg):
        yield cfg


def test_initialization_and_properties(mock_config):
    res = Resources()
    assert res.available_cores == 8
    assert res.total_cores == 8


def test_allocate_within_limits(mock_config):
    res = Resources()
    res.allocate_cores(3)
    assert res.available_cores == 5


def test_allocate_more_than_available_raises(mock_config):
    res = Resources()
    with pytest.raises(RuntimeError) as excinfo:
        res.allocate_cores(9)
    assert "allocate more core" in str(excinfo.value)


def test_free_within_limits(mock_config):
    res = Resources()
    res.allocate_cores(3)
    res.free_cores(2)
    assert res.available_cores == 7


def test_free_more_than_maximum_raises(mock_config):
    res = Resources()
    with pytest.raises(RuntimeError) as excinfo:
        res.free_cores(1)
    assert "free more cores" in str(excinfo.value)
