from .env import Env

class Context:
    """
    Context that "tags along" when excuting steps
    """

    def __init__(self, base_env=None):
        self.env = Env(base_env)
