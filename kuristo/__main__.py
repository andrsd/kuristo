import sys
import traceback

from rich.text import Text

import kuristo.cli as cli
import kuristo.config as config
import kuristo.ui as ui
from kuristo.exceptions import UserException


def main():
    parser = cli.build_parser()
    args = parser.parse_args()

    try:
        config.construct(args)

        if args.command == "run":
            exit_code = cli.run_jobs(args)
            sys.exit(exit_code)
        elif args.command == "doctor":
            cli.print_diag(args)
        elif args.command == "list":
            cli.list_jobs(args)
        elif args.command == "batch":
            cli.batch(args)
        elif args.command == "status":
            cli.status(args)
        elif args.command == "log":
            cli.log(args)
        elif args.command == "show":
            cli.show(args)
        elif args.command == "report":
            cli.report(args)
        elif args.command == "tag":
            cli.tag(args)
        elif args.command == "diff":
            cli.diff(args)
    except UserException as e:
        ui.console().print(Text(f"{e}", style="red"))
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
