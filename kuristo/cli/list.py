from rich.console import Console
from rich.text import Text
from .._utils import scan_locations, parse_workflow_files


def list_jobs(args):
    console = Console(force_terminal=not args.no_ansi, no_color=args.no_ansi, markup=not args.no_ansi)
    locations = args.location or ["."]

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)

    for sp in specs:
        name = Text.from_markup(sp.name, style="bold cyan")
        description = Text.from_markup(sp.description, style="dim")
        txt = Text("• ")
        txt.append(name)
        txt.append(": ")
        txt.append(description)
        console.print(txt)
    console.print()
    console.print(Text.from_markup(f"Found jobs: [green]{len(specs)}[/]"))
