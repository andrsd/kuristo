import kuristo.config as config
import kuristo.utils as utils
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime


def generate_junit(yaml_filename: Path, xml_filename: Path):
    report = utils.read_report(yaml_filename)

    results = report.get("results", [])

    tests = len(results)
    failures = sum(1 for r in results if r.get("status") == "failed")
    errors = sum(1 for r in results if r.get("status") == "error")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    time = sum(float(r.get("duration", 0)) for r in results)

    stat = yaml_filename.stat()
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

    try:
        format, filename = args.file.split(':')
    except ValueError:
        raise RuntimeError("Expected format of the file parameter is <format>:<filename>")

    run_name = args.run_id or "latest"
    runs_dir = cfg.log_dir / "runs" / run_name
    yaml_report = Path(runs_dir / "report.yaml")
    if not yaml_report.exists():
        raise RuntimeError("No report found. Did you run any jobs yet?")

    if format == "xml":
        generate_junit(yaml_report, Path(filename))
    else:
        raise RuntimeError(f"Requested unknown file format '{format}'")
