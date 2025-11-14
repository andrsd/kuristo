from kuristo.actions.shell_action import ShellAction
from kuristo.registry import get_action


class ActionFactory:
    """
    Build action from a job step specification
    """

    registered_actions = {}

    @staticmethod
    def create(step, context):
        working_directory = context.working_directory
        if context.defaults:
            if context.defaults.run:
                if context.defaults.run.working_directory:
                    working_directory = context.defaults.run.working_directory
        if step.working_directory:
            working_directory = step.working_directory

        if step.uses is None:
            return ShellAction(
                step.name,
                context,
                id=step.id,
                working_dir=working_directory,
                timeout_minutes=step.timeout_minutes,
                continue_on_error=step.continue_on_error,
                commands=step.run,
                num_cores=step.num_cores,
                env=step.env
            )
        elif get_action(step.uses):
            cls = get_action(step.uses)
            return cls(
                step.name,
                context,
                id=step.id,
                working_dir=working_directory,
                timeout_minutes=step.timeout_minutes,
                continue_on_error=step.continue_on_error,
                **step.params
            )
        else:
            raise RuntimeError(f"Requested unknown action: {step.uses}")
