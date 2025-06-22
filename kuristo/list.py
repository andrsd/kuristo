from rich.console import Console
from rich.text import Text
from ._utils import scan_locations, parse_workflow_files


console = Console()


def list_jobs(args):
    locations = args.location or ["."]

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)

    for sp in specs:
        name = Text(sp.name, style="bold cyan")
        description = Text(sp.description, style="dim")
        txt = Text("• ")
        txt.append(name)
        txt.append(": ")
        txt.append(description)
        console.print(txt)
    console.print()
    console.print(f"Found jobs: [green]{len(specs)}[/]")
