from pathlib import Path
import os
import platform
import sys
import subprocess
from rich.table import Table
from rich.text import Text
import kuristo.config as config
import kuristo.ui as ui
from kuristo.plugin_loader import find_kuristo_root, load_user_steps_from_kuristo_dir
from kuristo.registry import _ACTION_REGISTRY
from kuristo._version import __version__


def print_diag(args):
    console = ui.console()

    cfg = config.get()
    log_dir = cfg.log_dir
    runs_dir = log_dir / "runs"
    latest = runs_dir / "latest"

    load_user_steps_from_kuristo_dir()

    console.rule("Kuristo Diagnostic Report")

    # General
    table = Table(show_header=False, show_edge=False)
    table.add_row("Version", Text.from_markup(f"[cyan]{__version__}[/]"))
    table.add_row("Platform", f"{platform.system()} ({platform.processor()})")
    table.add_row("Python", f"{platform.python_version()} @ {sys.executable}")
    table.add_row("Config location", f"{cfg.path}")
    table.add_row("Log directory", f"{runs_dir}")
    table.add_row("Latest run", Text.from_markup(str(latest.resolve() if latest.exists() else "[dim]none[/]")))
    table.add_row("MPI launcher", Text.from_markup(f"[green]{cfg.mpi_launcher}[/]"))

    console.print(table)
    console.print()

    # Logging config
    console.print(Text.from_markup("[bold]Log Settings[/]"))
    log_table = Table(show_header=False, show_edge=False)
    log_table.add_row("Cleanup", Text.from_markup(f"[green]{cfg.log_cleanup}[/]"))
    log_table.add_row("History", str(cfg.log_history))
    console.print(log_table)
    console.print()

    # Resources
    console.print(Text.from_markup("[bold]Resources[/]"))
    try:
        output = subprocess.check_output(
            ["sysctl", "-n", "hw.perflevel0.physicalcpu"],
            text=True
        ) if sys.platform == "darwin" else None
        perf_cores = int(output.strip()) if output else None
    except Exception:
        perf_cores = None

    resource_table = Table(show_header=False, show_edge=False)
    resource_table.add_row("Cores (max used)", Text.from_markup(f"[cyan]{cfg.num_cores}[/]"))
    resource_table.add_row("System cores", str(os.cpu_count()))
    if perf_cores is not None:
        resource_table.add_row("Perf cores (macOS)", str(perf_cores))
    console.print(resource_table)
    console.print()

    # Plugins
    console.print(Text.from_markup("[bold]Plugins loaded[/]"))
    root = find_kuristo_root()
    if root:
        plugin_files = sorted(p.name for p in Path(root).glob("*.py"))
        if plugin_files:
            for pf in plugin_files:
                console.print(Text.from_markup(f"• [magenta]{pf}[/]"))
        else:
            console.print(Text.from_markup("[dim]No .py plugins found in .kuristo/[/]"))
    else:
        console.print(Text.from_markup("[dim]No .kuristo/ directory found[/]"))
    console.print()

    # Registered actions
    console.print(Text.from_markup("[bold]Actions registered[/]"))
    if _ACTION_REGISTRY:
        for name in sorted(_ACTION_REGISTRY):
            console.print(Text.from_markup(f"• [bold green]{name}[/]"))
    else:
        console.print(Text.from_markup("[dim]No actions registered[/]"))
    console.print()
