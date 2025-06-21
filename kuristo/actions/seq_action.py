from .._step import Step
from kuristo import action
from ..context import Context


@action("core/sequential")
class SeqAction(Step):
    """
    Run a sequential command
    """

    def __init__(self, name, cwd, timeout, context: Context, **kwargs) -> None:
        super().__init__(
            name=name,
            cwd=cwd,
            timeout=timeout,
            context=context
        )
        self._n_cores = kwargs.get("n_cores", 1)

    @property
    def num_cores(self):
        return self._n_cores

    def _create_command(self):
        command = 'echo seq'
        return command
