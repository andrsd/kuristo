from rich.text import Text
import kuristo.ui as ui
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations


def list_jobs(args):
    console = ui.console()
    locations = args.locations or ["."]

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)

    n_jobs = 0
    for sp in specs:
        job_names = sp.build_matrix_values()
        n_jobs += len(job_names)
        for name, _ in job_names:
            jnm = ui.job_name_markup(name)
            txt = Text("• ")
            txt.append(Text.from_markup(jnm, style="bold cyan"))
            txt.append(": ")
            txt.append(Text.from_markup(sp.description, style="dim"))
            console.print(txt)
    console.print()
    console.print(Text.from_markup(f"Found jobs: [green]{n_jobs}[/]"))
