import kuristo.config as config


class Resources:
    """
    Provides resources available to the framework
    """

    def __init__(self) -> None:
        cfg = config.get()
        self._max_cores = cfg.num_cores
        self._n_cores_available = self._max_cores

    @property
    def available_cores(self):
        return self._n_cores_available

    @property
    def total_cores(self):
        return self._max_cores

    def allocate_cores(self, n):
        if self._n_cores_available >= n:
            self._n_cores_available = self._n_cores_available - n
        else:
            raise RuntimeError("Trying to allocate more core then is available")

    def free_cores(self, n):
        if self._n_cores_available + n <= self._max_cores:
            self._n_cores_available = self._n_cores_available + n
        else:
            raise RuntimeError("Trying to free more cores then maximum available cores")
