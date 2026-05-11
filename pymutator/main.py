import argparse
import sys
import json
from os import cpu_count, path
from pathlib import Path
from .models import Config, Status
from .engine import start_mutators_process
from .report import report
from .runner import run_tests


class MutatorError(Exception):
    '''Base class for specific mutator errors.'''
    pass


class TestsFailed(MutatorError):
    '''Exception raised when the user's original tests fail'''
    pass


class SystemError(MutatorError):
    '''Exception raised for environment or infrastructure issues.'''
    pass


def main() -> None:
    '''
    The entry point to the application.
    Parses the arguments and starts the process.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--root", "-r", type=Path)
    parser.add_argument("file_path", nargs='?', type=Path)
    parser.add_argument("test_path", nargs='?', type=Path)
    parser.add_argument("--count", "-c", type=int, default=10)
    parser.add_argument("--timeout", "-t", type=int, default=5)
    parser.add_argument("--jobs", "-j", type=int, default=1)
    parser.add_argument("--max-jobs", action="store_true")
    parser.add_argument("--full-report", action="store_true")

    available = ", ".join(["Arithmetic", "Compare", "Constants", "BoolOp"])

    parser.add_argument(
        "--enabled", 
        nargs="+",
        default=["Arithmetic", "Compare", "Constants", "BoolOp"],
        help=f"A list of enabled mutators. Available: {available}"
    )

    args = parser.parse_args()

    if args.config:
        try:
            with open(args.config, "r") as f:
                data = json.load(f)
            config = Config(**data)
            
        except Exception as e:
            print(f"Configuration loading error: {e}")
            sys.exit(1)
    else:
        if not args.file_path or not args.test_path:
            print("Error: Specify the paths to the file and the tests, or use --config")
            sys.exit(1)
        file_abs = args.file_path.resolve()
        test_abs = args.test_path.resolve()

        if args.root:
            project_root = args.root.resolve()
        else:
            common = path.commonpath([str(file_abs), str(test_abs)])
            project_root = Path(common)


        if args.max_jobs:
            jobs_cnt = cpu_count()
        else:
            jobs_cnt = args.jobs

        config = Config(
            original_file_path=args.file_path.resolve(),
            test_dir=args.test_path.resolve(),
            timeout=args.timeout,
            mutant_cnt=args.count,
            jobs=jobs_cnt,
            full_report=args.full_report,
            root_path=project_root
        )


    source_code = config.original_file_path.read_text()
    try:
        try:
            status = run_tests(source_code, config)
        except Exception as e:
            raise SystemError() from e

        if status != Status.SURVIVED:
            raise TestsFailed()

    except SystemError as e:
        print(f"Pytest thrown exception: {e}")
        sys.exit(1)

    except TestsFailed as e:
        print(f"Test failed")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

    try:
        result = start_mutators_process(source_code, config)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

    finally:
        config.original_file_path.write_text(source_code)

    report(result, config)

if __name__ == "__main__":
    main()
