from .actions.shell import ShellAction
from .actions.function import FunctionStep
from .actions.mpi_action import MPIAction
from .actions.seq_action import SeqAction
from .registry import get_step, get_action


def register_actions():
    ActionFactory.register("core/sequential", SeqAction)
    ActionFactory.register("core/mpi", MPIAction)


class ActionFactory:
    """
    Build action from a test step specification
    """

    registered_actions = {}

    @staticmethod
    def create(ts):
        if ts.uses is None:
            return ShellAction(
                ts.name,
                ts.working_directory,
                ts.run
            )
        elif ts.uses in ActionFactory.registered_actions:
            return ActionFactory.registered_actions[ts.uses](
                ts.name,
                ts.working_directory,
                **ts.params
            )
        elif get_action(ts.uses):
            cls = get_action(ts.uses)
            return cls(
                ts.name,
                ts.working_directory,
                **ts.params
            )
        elif get_step(ts.uses):
            return FunctionStep(
                ts.name,
                ts.working_directory,
                ts.uses,
                **ts.params
            )
        else:
            raise RuntimeError(f"Requested unknown action: {ts.uses}")

    @staticmethod
    def register(name, klass):
        ActionFactory.registered_actions[name] = klass
