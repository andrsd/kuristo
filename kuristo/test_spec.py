class TestSpec:
    """
    Test specification
    """

    def __init__(self, n_cores=1) -> None:
        self._n_cores = n_cores

    @staticmethod
    def from_file(f):
        return [ TestSpec(), TestSpec() ]
