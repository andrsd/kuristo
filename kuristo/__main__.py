import sys
import kuristo.cli as cli


def main():
    parser = cli.build_parser()
    args = parser.parse_args()

    if args.command == "run":
        exit_code = cli.run_jobs(args)
        sys.exit(exit_code)
    elif args.command == "doctor":
        cli.print_diag(args)
    elif args.command == "list":
        cli.list_jobs(args)


if __name__ == "__main__":
    main()
