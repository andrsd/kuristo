from rich.console import Console
from rich.text import Text
from ._utils import scan_locations, parse_tests_files


console = Console()


def list_tests(args):
    locations = args.location or ["."]

    tests_files = scan_locations(locations)
    tests = parse_tests_files(tests_files)

    for ts in tests:
        name = Text(ts.name, style="bold cyan")
        description = Text(ts.description, style="dim")
        txt = Text("• ")
        txt.append(name)
        txt.append(": ")
        txt.append(description)
        console.print(txt)
    console.print()
    console.print(f"Found tests: [green]{len(tests)}[/]")
