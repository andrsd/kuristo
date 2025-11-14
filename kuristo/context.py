from kuristo.env import Env


class Context:
    """
    Context that "tags along" when excuting steps
    """

    def __init__(self, base_env=None, defaults=None, matrix=None):
        self.env = Env(base_env)
        self.defaults = defaults
        # variables for substitution
        self.vars = {
            "matrix": matrix,
            "steps": {}
        }
