import subprocess
import tempfile
import os
import shutil
from .models import Config, Status
from pathlib import Path

def run_tests(code: str, config: Config) -> Status:
    """
    Substitute original code with mutant, run pytest and restore the original.

    Args:
        code (str): The mutated source code to be tested.
        config (Config): Configuration containing paths and timeout settings.

    Returns:
        Status: The result of the mutation test (KILLED, SURVIVED, or TIMEOUT).
    

    original_code = config.original_file_path.read_text()

    config.original_file_path.write_text(code)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.bak', delete=False) as temp:
        temp.write(original_code)
        temp.flush()
        temp_path = Path(temp.name)

    try:
        code_dir = str(config.original_file_path.parent)
        test_dir = str(config.test_dir)
        new_paths = [code_dir, test_dir]

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        current_pythonpath = env.get("PYTHONPATH", "")

        if current_pythonpath:
            env["PYTHONPATH"] = os.pathsep.join(new_paths) + os.pathsep + current_pythonpath
        else:
            env["PYTHONPATH"] = os.pathsep.join(new_paths)

        result = subprocess.run(
            ["pytest", "-q", "--no-header", config.test_dir],
            capture_output=True,
            cwd=str(config.original_file_path.parent),
            text=True,
            timeout=config.timeout,
            env=env
        )

        if result.returncode == 0:
            return Status.SURVIVED
        else:
            return Status.KILLED

    except subprocess.TimeoutExpired:
        return Status.TIMEOUT

    finally:
        config.original_file_path.write_text(temp_path.read_text())
        temp_path.unlink()
    """

    rel_file = config.original_file_path.relative_to(config.root_path)
    rel_test = config.test_dir.relative_to(config.root_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copytree(config.root_path, Path(tmp_dir), dirs_exist_ok=True, 
                        ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'venv', '.git'))

        mutant_path = Path(tmp_dir) / rel_file
        mutant_path.write_text(code)

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(Path(tmp_dir))

        try:
            result = subprocess.run(
                ["pytest", "-q", "--no-header", "-x", str(Path(tmp_dir) / rel_test)],
                cwd=str(Path(tmp_dir)),
                env=env,
                capture_output=True,
                text=True,
                timeout=config.timeout
            )

            if result.returncode == 0:
                return Status.SURVIVED
            else:
                return Status.KILLED
        except subprocess.TimeoutExpired:
            return Status.TIMEOUT
    