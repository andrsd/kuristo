import kuristo.config as config
import kuristo.utils as utils
import kuristo.cli._show as show
import kuristo.ui as ui
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime


def generate_junit(results, xml_filename: Path, stat):
    tests = len(results)
    failures = sum(1 for r in results if r.get("status") == "failed")
    errors = sum(1 for r in results if r.get("status") == "error")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    time = sum(float(r.get("duration", 0)) for r in results)

    created = datetime.fromtimestamp(stat.st_ctime).isoformat()

    testsuites = ET.Element("testsuites")
    testsuite = ET.SubElement(
        testsuites,
        "testsuite",
        name="TestResults",
        tests=str(tests),
        failures=str(failures),
        errors=str(errors),
        skipped=str(skipped),
        time=f"{time:.3f}",
        timestamp=created
    )

    for r in results:
        testcase = ET.SubElement(
            testsuite,
            "testcase",
            classname="jobs",
            name=r.get("job-name", f"id-{r.get('id')}"),
            time=f"{float(r.get('duration', 0)):.3f}"
        )

        if r.get("status") == "failed":
            ET.SubElement(
                testcase,
                "failure",
                message=f"Process completed with exit code {r.get('return-code')}"
            ).text = "Failed"
        elif r.get("status") == "skipped":
            ET.SubElement(
                testcase,
                "skipped",
                message=f"{r.get('reason')}"
            )

    tree = ET.ElementTree(testsuites)
    tree.write(xml_filename, encoding="utf-8", xml_declaration=True)


def report(args):
    cfg = config.get()

    run_name = args.run_id or "latest"
    runs_dir = cfg.log_dir / "runs" / run_name
    report_path = Path(runs_dir / "report.yaml")
    if not report_path.exists():
        raise RuntimeError("No report found. Did you run any jobs yet?")

    report = utils.read_report(report_path)
    filters = utils.build_filters(args)

    results = report.get("results", [])
    if len(filters) == 0:
        filtered = results
    else:
        filtered = [r for r in results if r["status"] in filters]

    if args.output:
        try:
            format, filename = args.output.split(':')
        except ValueError:
            raise RuntimeError("Expected format of the file parameter is <format>:<filename>")

        if format == "xml":
            stat = report_path.stat()
            generate_junit(filtered, Path(filename), stat)
        else:
            raise RuntimeError(f"Requested unknown file format '{format}'")
    else:
        # write to terminal
        for entry in filtered:
            log_path = Path(runs_dir / f"job-{entry['id']}.log")
            if len(filters) == 0:
                ui.job_header_line(entry['id'], cfg.console_width)
                show.display_job_log(log_path)
            elif entry['status'] in filters:
                ui.job_header_line(entry['id'], cfg.console_width)
                show.display_job_log(log_path, filters)
