import pytest

from kuristo.batch import get_backend
from kuristo.exceptions import UserException


def test_get_backend_valid():
    backend = get_backend("slurm")
    assert backend.name == "slurm"


def test_get_backend_none():
    with pytest.raises(UserException):
        get_backend(None)


def test_get_backend_invalid():
    with pytest.raises(UserException):
        get_backend("invalid_backend")
