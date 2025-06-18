import importlib.util
import pathlib
import sys


def find_kuristo_root(start_path=None):
    """
    Search up from start_path (or cwd) to find the first directory containing `.kuristo/`
    """
    current = pathlib.Path(start_path or pathlib.Path.cwd()).resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".kuristo").is_dir():
            return parent / ".kuristo"

    return None


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
