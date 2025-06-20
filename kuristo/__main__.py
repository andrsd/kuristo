import sys
from .cli import build_cli
from .run import run_tests
from .doctor import print_diag
from .list import list_tests


def main():
    parser = build_cli()
    args = parser.parse_args()

    if args.command == "run":
        exit_code = run_tests(args)
        sys.exit(exit_code)
    elif args.command == "doctor":
        print_diag()
    elif args.command == "list":
        list_tests(args)


if __name__ == "__main__":
    main()
