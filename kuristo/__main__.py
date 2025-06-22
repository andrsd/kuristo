import sys
from .cli import build_cli
from .run import run_jobs
from .doctor import print_diag
from .list import list_jobs


def main():
    parser = build_cli()
    args = parser.parse_args()

    if args.command == "run":
        exit_code = run_jobs(args)
        sys.exit(exit_code)
    elif args.command == "doctor":
        print_diag()
    elif args.command == "list":
        list_jobs(args)


if __name__ == "__main__":
    main()
