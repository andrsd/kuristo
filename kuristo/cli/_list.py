from rich.text import Text
import kuristo.ui as ui
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations


def list_jobs(args):
    console = ui.console()
    locations = args.locations or ["."]

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
