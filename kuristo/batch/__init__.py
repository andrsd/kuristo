from .backend import BatchBackend
from .slurm import SlurmBackend


BACKENDS = {
    "slurm": SlurmBackend,
}


def get_backend(name, **kwargs) -> BatchBackend:
    try:
        if name is None:
            raise RuntimeError("No queue backend specified, use --backend switch to specify one.")
        backend_cls = BACKENDS.get(name.lower())
        if backend_cls is None:
            raise ValueError(f"Unsupported backend: {name}")
        return backend_cls(**kwargs)
    except Exception as e:
        print(e)
        exit(-1)
