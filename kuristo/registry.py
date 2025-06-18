_STEP_REGISTRY = {}
_ACTION_REGISTRY = {}


def step(name):
    """
    Function decorator, so we can do @kuristo.step(name) and have users to use
    such function from their yaml workflow files
    """
    def decorator(fn):
        _STEP_REGISTRY[name] = fn
        return fn
    return decorator


def get_step(name):
    return _STEP_REGISTRY[name]


def action(name):
    """
    Class decorator, so we can do @kuristo.action(name) and have users define
    a Step-derived class that they can use from their yaml workflow files
    """
    def decorator(cls):
        _ACTION_REGISTRY[name] = cls
        return cls
    return decorator


def get_action(name):
    return _ACTION_REGISTRY.get(name)
