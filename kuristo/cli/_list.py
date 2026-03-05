from rich.text import Text

import kuristo.ui as ui
import kuristo.utils as utils
from kuristo.scanner import scan_locations
from kuristo.workflow import parse_workflow_files


def list_jobs(args):
    console = ui.console()
    locations = args.locations or ["."]

    workflow_files = scan_locations(locations)
    workflows = parse_workflow_files(workflow_files)

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
                job_display_name = utils.render_job_name(sp, variant)
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
