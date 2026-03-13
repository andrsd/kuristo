from kuristo.batch.backend import BatchBackend
from kuristo.batch.slurm import SlurmBackend
from kuristo.exceptions import UserException

BACKENDS = {
    "slurm": SlurmBackend,
}


def get_backend(name, **kwargs) -> BatchBackend:
    if name is None:
        raise UserException("No queue backend specified, use --backend switch to specify one.")
    backend_cls = BACKENDS.get(name.lower())
    if backend_cls is None:
        raise UserException(f"Unsupported backend: {name}")
    return backend_cls(**kwargs)
