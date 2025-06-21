from .actions.shell import ShellAction
from .actions.function import FunctionStep
from .registry import get_step, get_action


class ActionFactory:
    """
    Build action from a test step specification
    """

    registered_actions = {}

    @staticmethod
    def create(ts, context):
        if ts.uses is None:
            return ShellAction(
                ts.name,
                ts.working_directory,
                ts.timeout_minutes,
                context,
                ts.run,
            )
        elif get_action(ts.uses):
            cls = get_action(ts.uses)
            return cls(
                ts.name,
                ts.working_directory,
                ts.timeout_minutes,
                context,
                **ts.params
            )
        elif get_step(ts.uses):
            return FunctionStep(
                ts.name,
                ts.working_directory,
                ts.timeout_minutes,
                context,
                ts.uses,
                **ts.params
            )
        else:
            raise RuntimeError(f"Requested unknown action: {ts.uses}")
