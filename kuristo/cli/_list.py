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
        if sp.strategy:
            job_names = sp.build_matrix_values()
        else:
            job_names = [(sp.id, None)]
        n_jobs += len(job_names)
        for name, _ in job_names:
            jnm = ui.job_name_markup(name)
            txt = Text("")
            if sp.skip:
                txt.append(Text.from_markup(f"• {jnm}: {sp.name}", style="grey35"))
            else:
                txt.append(Text.from_markup("• "))
                txt.append(Text.from_markup(jnm, style="bold cyan"))
                txt.append(": ")
                txt.append(Text.from_markup(sp.name, style="grey70"))
            console.print(txt)
    console.print()
    console.print(Text.from_markup(f"Found jobs: [green]{n_jobs}[/]"))
