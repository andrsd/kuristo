from kuristo.actions.shell_action import ShellAction
from kuristo.exceptions import UserException
from kuristo.registry import get_action
from kuristo.utils import interpolate_value


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
            commands = step.run
            if context is not None:
                commands = interpolate_value(commands, context.vars)
            return ShellAction(
                step.name,
                context,
                id=step.id,
                working_dir=working_directory,
                timeout_minutes=step.timeout_minutes,
                continue_on_error=step.continue_on_error,
                commands=commands,
                num_cores=step.num_cores,
                env=step.env,
            )
        elif get_action(step.uses):
            cls = get_action(step.uses)
            params = step.params
            if context is not None:
                params = interpolate_value(params, context.vars)
            return cls(
                step.name,
                context,
                id=step.id,
                working_dir=working_directory,
                timeout_minutes=step.timeout_minutes,
                continue_on_error=step.continue_on_error,
                **params,
            )
        else:
            raise UserException(f"Requested unknown action: {step.uses}")
