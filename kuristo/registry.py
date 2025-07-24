_ACTION_REGISTRY = {}


def action(name):
    """
    Class decorator, so we can do @kuristo.action(name) and have users define
    a Action-derived class that they can use from their yaml workflow files
    """
    def decorator(cls):
        _ACTION_REGISTRY[name] = cls
        return cls
    return decorator


def get_action(name):
    return _ACTION_REGISTRY.get(name)
