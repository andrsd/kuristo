import pytest
from kuristo.batch import get_backend


def test_get_backend_valid():
    backend = get_backend("slurm")
    assert backend.name == "slurm"


def test_get_backend_none():
    with pytest.raises(RuntimeError):
        get_backend(None)


def test_get_backend_invalid():
    with pytest.raises(ValueError):
        get_backend("invalid_backend")
