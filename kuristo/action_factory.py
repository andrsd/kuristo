from kuristo.actions.shell_action import ShellAction
from kuristo.registry import get_action


class ActionFactory:
    """
    Build action from a job step specification
    """

    registered_actions = {}

    @staticmethod
    def create(step, context):
        if step.uses is None:
            return ShellAction(
                step.name,
                context,
                id=step.id,
                working_dir=step.working_directory,
                timeout_minutes=step.timeout_minutes,
                continue_on_error=step.continue_on_error,
                commands=step.run,
            )
        elif get_action(step.uses):
            cls = get_action(step.uses)
            return cls(
                step.name,
                context,
                id=step.id,
                working_dir=step.working_directory,
                timeout_minutes=step.timeout_minutes,
                continue_on_error=step.continue_on_error,
                **step.params
            )
        else:
            raise RuntimeError(f"Requested unknown action: {step.uses}")
