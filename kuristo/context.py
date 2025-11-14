from kuristo.env import Env


class Context:
    """
    Context that "tags along" when excuting steps
    """

    def __init__(self, base_env=None, working_directory=None, defaults=None, matrix=None):
        self.env = Env(base_env)
        self.working_directory = working_directory
        self.defaults = defaults
        # variables for substitution
        self.vars = {
            "matrix": matrix,
            "steps": {}
        }
