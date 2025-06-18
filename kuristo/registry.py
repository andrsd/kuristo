_STEP_REGISTRY = {}


def step(func=None, *, name=None):
    def decorator(f):
        step_name = name or f.__name__
        _STEP_REGISTRY[step_name] = f
        return f

    if func is None:
        return decorator
    else:
        return decorator(func)


def get_step(name):
    return _STEP_REGISTRY[name]
