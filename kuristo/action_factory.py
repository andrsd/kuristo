from .actions.shell_action import ShellAction
from .registry import get_action


class ActionFactory:
    """
    Build action from a job step specification
    """

    registered_actions = {}

    @staticmethod
    def create(ts, context):
        if ts.uses is None:
            return ShellAction(
                ts.name,
                context,
                id=ts.id,
                working_dir=ts.working_directory,
                timeout_minutes=ts.timeout_minutes,
                commands=ts.run,
            )
        elif get_action(ts.uses):
            cls = get_action(ts.uses)
            return cls(
                ts.name,
                context,
                id=ts.id,
                working_dir=ts.working_directory,
                timeout_minutes=ts.timeout_minutes,
                **ts.params
            )
        else:
            raise RuntimeError(f"Requested unknown action: {ts.uses}")
