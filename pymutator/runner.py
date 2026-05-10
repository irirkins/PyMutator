import subprocess
import tempfile
import os
import shutil
import psutil
import time
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

        proc = None
        try:
            proc = subprocess.Popen(
                ["pytest", "-q", "--no-header", "-x", str(Path(tmp_dir) / rel_test)],
                cwd=str(Path(tmp_dir)),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            ps_proc = psutil.Process(proc.pid)
            start_time = time.time()

            while proc.poll() is None:
                if time.time() - start_time > config.timeout:
                    proc.kill()
                    return Status.TIMEOUT

                mem_usage = ps_proc.memory_info().rss
                    
                if mem_usage > 512 * 1024 * 1024:
                    proc.kill()
                    return Status.TIMEOUT
                        
                time.sleep(0.1)

            if proc.returncode == 0:
                return Status.SURVIVED
            return Status.KILLED

        except Exception:
            return Status.KILLED

        finally:
            if proc and proc.poll() is None:
                proc.kill()