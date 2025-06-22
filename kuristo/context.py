from .env import Env
from .config import Config


class Context:
    """
    Context that "tags along" when excuting steps
    """

    def __init__(self, config: Config, base_env=None, matrix=None):
        self.config = config
        self.env = Env(base_env)
        # variables for substitution
        self.vars = {
            "matrix": matrix,
            "steps": {}
        }
