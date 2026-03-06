from rich.text import Text

import kuristo.ui as ui
import kuristo.utils as utils
from kuristo.scanner import scan_locations
from kuristo.utils import filter_specs_by_labels
from kuristo.workflow import parse_workflow_files


def list_jobs(args):
    console = ui.console()
    locations = args.locations or ["."]

    workflow_files = scan_locations(locations)
    workflows = parse_workflow_files(workflow_files)

    # Filter by labels if specified
    requested_labels = getattr(args, "labels", None)
    if requested_labels:
        specs, total_jobs, filtered_jobs = filter_specs_by_labels(workflows, requested_labels)
        console.print(
            f"[cyan]Showing {filtered_jobs} of {total_jobs} jobs matching labels:[/] [magenta]{', '.join(requested_labels)}[/]"
        )

    n_jobs = 0
    for wf in workflows:
        for sp in wf.jobs.values():
            if sp.strategy:
                job_names = sp.build_matrix_values()
            else:
                job_names = [(sp.id, None)]
            n_jobs += len(job_names)
            for name, variant in job_names:
                jnm = ui.job_name_markup(name)
                # Interpolate job name with matrix variables if present
                job_display_name = sp.name
                if variant:
                    job_display_name = utils.interpolate_str(sp.name, {"matrix": variant})
                txt = Text("")
                if sp.skip:
                    txt.append(Text.from_markup(f"• {jnm}: {job_display_name}", style="grey35"))
                else:
                    txt.append(Text.from_markup("• "))
                    txt.append(Text.from_markup(jnm, style="bold cyan"))
                    txt.append(": ")
                    txt.append(Text.from_markup(job_display_name, style="grey70"))
                    if sp.labels:
                        txt.append(Text.from_markup(f" ({', '.join(sp.labels)})", style="magenta"))
                console.print(txt)
    console.print()
    console.print(Text.from_markup(f"Found jobs: [green]{len(workflows)}[/]"))
