from pathlib import Path
import os
import platform
import sys
import subprocess
from rich.console import Console
from rich.table import Table
from .config import Config
from ._plugin_loader import find_kuristo_root, load_user_steps_from_kuristo_dir
from .registry import _STEP_REGISTRY, _ACTION_REGISTRY
from .action_factory import register_actions
from kuristo import __version__


console = Console()


def print_diag():
    config = Config()
    log_dir = config.log_dir
    runs_dir = log_dir / "runs"
    latest = runs_dir / "latest"

    register_actions()
    load_user_steps_from_kuristo_dir()

    console.rule("Kuristo Diagnostic Report")

    # General
    table = Table(show_header=False, show_edge=False)
    table.add_row("Version", f"[cyan]{__version__}[/]")
    table.add_row("Platform", f"{platform.system()} ({platform.processor()})")
    table.add_row("Python", f"{platform.python_version()} @ {sys.executable}")
    table.add_row("Config location", f"{config.path}")
    table.add_row("Log directory", f"{runs_dir}")
    table.add_row("Latest run", str(latest.resolve() if latest.exists() else "[dim]none[/]"))

    console.print(table)
    console.print()

    # Logging config
    console.print("[bold]Log Settings[/]")
    log_table = Table(show_header=False, show_edge=False)
    log_table.add_row("Cleanup", f"[green]{config.log_cleanup}[/]")
    log_table.add_row("History", str(config.log_history))
    console.print(log_table)
    console.print()

    # Resources
    console.print("[bold]Resources[/]")
    try:
        output = subprocess.check_output(
            ["sysctl", "-n", "hw.perflevel0.physicalcpu"],
            text=True
        ) if sys.platform == "darwin" else None
        perf_cores = int(output.strip()) if output else None
    except Exception:
        perf_cores = None

    resource_table = Table(show_header=False, show_edge=False)
    resource_table.add_row("Cores (max used)", f"[cyan]{config.num_cores}[/]")
    resource_table.add_row("System cores", str(os.cpu_count()))
    if perf_cores is not None:
        resource_table.add_row("Perf cores (macOS)", str(perf_cores))
    console.print(resource_table)
    console.print()

    # Plugins
    console.print("[bold]Plugins loaded[/]")
    root = find_kuristo_root()
    if root:
        plugin_files = sorted(p.name for p in Path(root).glob("*.py"))
        if plugin_files:
            for pf in plugin_files:
                console.print(f"• [magenta]{pf}[/]")
        else:
            console.print("[dim]No .py plugins found in .kuristo/[/]")
    else:
        console.print("[dim]No .kuristo/ directory found[/]")
    console.print()

    # Registered steps
    console.print("[bold]Steps registered[/]")
    if _STEP_REGISTRY:
        for name in sorted(_STEP_REGISTRY):
            console.print(f"• [bold cyan]{name}[/]")
    else:
        console.print("[dim]No steps registered[/]")
    console.print()

    # Registered actions
    console.print("[bold]Actions registered[/]")
    if _ACTION_REGISTRY:
        for name in sorted(_ACTION_REGISTRY):
            console.print(f"• [bold green]{name}[/]")
    else:
        console.print("[dim]No actions registered[/]")
    console.print()
