class Resources:
    """
    Provides resources available to the testing
    """

    def __init__(self) -> None:
        self._n_cores_available = 8
        self._max_cores = 8

    @property
    def available_cores(self):
        return self._n_cores_available

    def allocate_cores(self, n):
        if self._n_cores_available >= n:
            self._n_cores_available = self._n_cores_available - n
        else:
            raise SystemError("Trying to allocate more core then is available")

    def free_cores(self, n):
        if self._n_cores_available + n <= self._max_cores:
            self._n_cores_available = self._n_cores_available + n
        else:
            raise SystemError("Trying to free more cores then maximum available cores")
