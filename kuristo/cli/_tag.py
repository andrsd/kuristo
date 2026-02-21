from rich.table import Table

import kuristo.config as config
import kuristo.ui as ui
import kuristo.utils as utils


def tag_add(args):
    """Add a tag to a run"""
    if args.name is None:
        raise RuntimeError("Tag name is required")

    cfg = config.get()
    runs_dir = cfg.log_dir / "runs"

    # Determine run ID
    if args.run_id:
        run_id = args.run_id
    else:
        # Use latest run
        latest_link = runs_dir / "latest"
        if not latest_link.is_symlink():
            raise RuntimeError("No runs found. Cannot tag non-existent run.")
        run_id = latest_link.resolve().name

    utils.create_tag(cfg.log_dir, args.name, run_id)

    console = ui.console()
    console.print(f"Tagged run '[cyan]{run_id}[/]' as '[green]{args.name}[/]'")


def tag_delete(args):
    """Delete a tag"""
    if args.name is None:
        raise RuntimeError("Tag name is required for deletion")

    cfg = config.get()
    utils.delete_tag(cfg.log_dir, args.name)

    console = ui.console()
    console.print(f"Deleted tag '[green]{args.name}[/]'")


def tag_list(args):
    """List all tags"""
    cfg = config.get()
    tags = utils.list_tags(cfg.log_dir)

    if not tags:
        console = ui.console()
        console.print("[dim]No tags found[/]")
        return

    console = ui.console()
    table = Table(show_lines=False, box=None)
    table.add_column("Tag", style="bold green", no_wrap=True)
    table.add_column("Run ID", style="cyan")

    for tag_name, run_id in tags:
        table.add_row(tag_name, run_id)

    console.print(table)


def tag(args):
    """Main tag command dispatcher"""
    if args.list_tags:
        tag_list(args)
    elif args.delete:
        tag_delete(args)
    else:
        tag_add(args)
