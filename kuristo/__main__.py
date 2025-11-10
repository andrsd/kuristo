import sys
import kuristo.cli as cli
import kuristo.config as config


def main():
    try:
        parser = cli.build_parser()
        args = parser.parse_args()

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
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
