from .actions.shell import ShellAction


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
        else:
            raise RuntimeError(f"Requested unknown action: {ts.uses}")

    @staticmethod
    def register(name, klass):
        ActionFactory.registered_actions[name] = klass
