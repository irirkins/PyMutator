import argparse
import sys
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
    parser.add_argument("file_path", type=Path)
    parser.add_argument("test_path", type=Path)
    parser.add_argument("--count", "-c", type=int, default=10)
    parser.add_argument("--timeout", "-t", type=int, default=5)

    args = parser.parse_args()
    config = Config(
        original_file_path=args.file_path.resolve(),
        test_dir=args.test_path.resolve(),
        timeout=args.timeout,
        mutant_cnt=args.count
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

    result = start_mutators_process(source_code, config)
    report(result)

if __name__ == "__main__":
    main()