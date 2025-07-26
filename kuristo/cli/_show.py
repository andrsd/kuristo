from kuristo.config import Config
import kuristo.utils as utils
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.text import Text


def parse_log_line(line):
    parts = line.strip().split(" - ", 2)
    if len(parts) != 3:
        return None
    timestamp_str, tag, msg = parts
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
    except ValueError:
        return None
    return timestamp, tag.strip(), msg.strip()


def parse_sections(lines):
    title = None
    sections = []
    current = None

    for timestamp, tag, msg in lines:
        if tag == 'TASK_START':
            if current:
                sections.append(current)
            current = {
                "type": "section",
                "title": msg[2:].strip(),
                "lines": [],
                "return_code": None,
                "start_time": timestamp,
                "end_time": None
            }
        elif tag == 'TASK_END':
            rc = int(msg.split("return code")[1].strip())
            if current:
                current["return_code"] = rc
                current["end_time"] = timestamp
        elif msg.startswith("|"):
            if current:
                current["lines"].append(("ENV_VAR", msg[2:].strip()))
        elif tag == 'JOB_START':
            title = {
                "type": "title",
                "title": msg,
                "start_time": timestamp,
                "end_time": None
            }
            sections.append(title)
        elif tag == 'JOB_END':
            if title:
                title["end_time"] = timestamp
        else:
            if current:
                current["lines"].append((tag, msg))

    if current:
        sections.append(current)

    return sections


def render_title(console: Console, sec, max_label_len):
    title = sec["title"]

    tm = 0.
    if sec["start_time"] and sec["end_time"]:
        tm = (sec["end_time"] - sec["start_time"]).total_seconds()
    time_str = utils.human_time2(tm)

    wd = max_label_len - 8 - len(title) - len(time_str)
    dots = "." * wd

    txt = f"Name: [white]{title}[/] [grey23]{dots}[/] [white]{time_str}[/]"
    console.print(Text.from_markup(txt))
    console.print()


def render_section(console: Console, sec, max_label_len):
    title = sec["title"]

    rc = sec["return_code"]
    status = "PASS" if rc == 0 else "FAIL"
    if status == "SKIP":
        st = "[yellow]SKIP[/]"
    elif status == "PASS":
        st = "[green]PASS[/]"
    elif status == "FAIL" or status == "TIMEOUT":
        st = "[red]FAIL[/]"
    else:
        st = ""

    delta = 0.
    if sec["start_time"] and sec["end_time"]:
        delta = (sec["end_time"] - sec["start_time"]).total_seconds()
    time_str = utils.human_time2(delta)

    wd = max_label_len - 9 - len(title) - len(time_str)
    dots = "." * wd

    header = f"[white]*[/] {st} {title} [grey23]{dots}[/] [white]{time_str}[/]"
    console.print(Text.from_markup(header))

    for tag, msg in sec["lines"]:
        if tag == "SCRIPT":
            console.print(Text.from_markup(f"  [grey46]{msg}[/]"))
        elif tag == "OUTPUT":
            console.print(Text.from_markup(f"  {msg}"))
        elif "passed" in msg.lower():
            console.print(Text.from_markup(f"  {msg}"))
        elif "failed" in msg.lower():
            console.print(Text.from_markup(f"  {msg}"))
        elif tag == "ENV":
            console.print(Text.from_markup(""))
            console.print(Text.from_markup("[white]*[/] Environment variables:"))
        elif tag == "ENV_VAR":
            console.print(Text.from_markup(f"  [grey63]{msg}[/]"))
        else:
            console.print(Text.from_markup(f"  {msg}"))
    console.print()


def render_sections(console: Console, sections, config: Config):
    max_label_len = config.console_width
    for sec in sections:
        if sec["type"] == "title":
            render_title(console, sec, max_label_len)
        else:
            render_section(console, sec, max_label_len)


def display_job_log(console: Console, log_path: Path, config: Config):
    if not log_path.exists():
        raise RuntimeError(f"Log file not found: {log_path}")

    with open(log_path) as f:
        lines = [parse_log_line(line) for line in f if parse_log_line(line)]

    sections = parse_sections(lines)
    render_sections(console, sections, config)


def show(args):
    try:
        console = Console(force_terminal=not args.no_ansi, no_color=args.no_ansi, markup=not args.no_ansi)

        config = Config()
        run_name = args.run or "latest"
        runs_dir = config.log_dir / "runs" / run_name

        log_path = Path(runs_dir / f"job-{args.job}.log")
        display_job_log(console, log_path, config)
    except Exception as e:
        print(e)
