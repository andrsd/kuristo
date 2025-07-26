from kuristo.actions.process_action import ProcessAction
from kuristo.registry import action
from kuristo.context import Context


@action("core/sequential")
class SeqAction(ProcessAction):
    """
    Run a sequential command
    """

    def __init__(self, name, context: Context, **kwargs) -> None:
        super().__init__(
            name=name,
            context=context,
            **kwargs
        )
        self._n_cores = kwargs.get("n_cores", 1)

    @property
    def num_cores(self):
        return self._n_cores

    def create_command(self):
        command = 'echo seq'
        return command
