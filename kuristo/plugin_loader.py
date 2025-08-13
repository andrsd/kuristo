import importlib.util
import sys
from kuristo.utils import find_kuristo_root


def load_user_steps_from_kuristo_dir():
    kuristo_dir = find_kuristo_root()
    if not kuristo_dir:
        return

    for file in kuristo_dir.glob("*.py"):
        module_name = f"_kuristo_user_{file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(file))
        if spec is not None:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
        else:
            raise RuntimeError(f"Failed to load {file}")
