from rich.text import Text

import kuristo.ui as ui
from kuristo.job_spec import parse_workflow_files
from kuristo.scanner import scan_locations
from kuristo.utils import filter_specs_by_labels


def list_jobs(args):
    console = ui.console()
    locations = args.locations or ["."]

    workflow_files = scan_locations(locations)
    specs = parse_workflow_files(workflow_files)

    # Filter by labels if specified
    requested_labels = getattr(args, "labels", None)
    if requested_labels:
        specs, total_jobs, filtered_jobs = filter_specs_by_labels(specs, requested_labels)
        console.print(
            f"[cyan]Showing {filtered_jobs} of {total_jobs} jobs matching labels:[/] [magenta]{', '.join(requested_labels)}[/]"
        )

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
                if sp.labels:
                    txt.append(Text.from_markup(f" ({', '.join(sp.labels)})", style="magenta"))
            console.print(txt)
    console.print()
    console.print(Text.from_markup(f"Found jobs: [green]{n_jobs}[/]"))
