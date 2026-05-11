import pytest
from pymutator.engine import start_mutators_process
from pymutator.runner import run_tests
from pymutator.models import Config, Status

def setup_test_project(tmp_path, code, test_code):
    """Helper to create a temporary project on disk."""
    project = tmp_path / "project"
    project.mkdir()
    logic = project / "logic.py"
    logic.write_text(code)
    tests = project / "tests"
    tests.mkdir()
    test_file = tests / "test_logic.py"
    test_file.write_text(test_code)
    return logic, tests, project

def test_runner_status_killed(tmp_path):
    """Test full cycle where mutant is killed by AssertionError."""
    logic, tests, root = setup_test_project(tmp_path, "def f(a, b): return a + b", 
                                            "from logic import f\ndef test_f(): assert f(1, 1) == 2")
    config = Config(original_file_path=logic, test_dir=tests, root_path=root, jobs=1)
    status = run_tests("def f(a, b): return a - b", config)
    assert status == Status.KILLED

def test_runner_status_survived(tmp_path):
    """Test full cycle where mutant survives due to weak tests."""
    logic, tests, root = setup_test_project(tmp_path, "def f(a): return a + 0", 
                                            "from logic import f\ndef test_f(): assert f(5) == 5")
    config = Config(original_file_path=logic, test_dir=tests, root_path=root, jobs=1)
    status = run_tests("def f(a): return a - 0", config)
    assert status == Status.SURVIVED

def test_runner_status_timeout(tmp_path):
    """Test the watchdog timer for infinite loops."""
    logic, tests, root = setup_test_project(tmp_path, "def f(): return 1", 
                                            "from logic import f\ndef test_f(): f()")
    config = Config(original_file_path=logic, test_dir=tests, root_path=root, timeout=1)
    infinite_loop = "def f():\n    while True: pass"
    status = run_tests(infinite_loop, config)
    assert status == Status.TIMEOUT

def test_memory_limit_hit(tmp_path):
    """Test the memory watchdog using psutil monitoring."""
    logic, tests, root = setup_test_project(tmp_path, "def f(): return 1", 
                                            "from logic import f\ndef test_f(): f()")
    config = Config(original_file_path=logic, test_dir=tests, root_path=root, timeout=10)
    leak_code = "def f():\n    data = []\n    while True: data.append(' ' * 10**6)"
    status = run_tests(leak_code, config)
    assert status == Status.TIMEOUT

@pytest.mark.parametrize("jobs", [1, 4])
def test_engine_execution_modes(tmp_path, jobs):
    """Test both sequential and parallel engine execution."""
    code = "x = 1 + 2\ny = 3 + 4"
    logic, tests, root = setup_test_project(tmp_path, code, 
                                            "from logic import x\ndef test_x(): assert True")
    config = Config(original_file_path=logic, test_dir=tests, root_path=root, jobs=jobs, mutant_cnt=2)
    results = start_mutators_process(code, config)
    assert len(results) == 2

def test_engine_zero_mutants_requested(tmp_path):
    """Verify behavior when user requests zero mutants."""
    f = tmp_path / "f.py"
    f.write_text("x = 1 + 2") 
    config = Config(original_file_path=tmp_path/"f.py", test_dir=tmp_path, root_path=tmp_path, mutant_cnt=0)
    assert start_mutators_process("x = 1 + 2", config) == []