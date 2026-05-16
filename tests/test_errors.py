import pytest
from pathlib import Path
from pymutator.models import Config

def test_pydantic_validation_error():
    """Check that Pydantic prevents invalid configuration."""
    with pytest.raises(Exception):
        Config(original_file_path=Path("non_existent.py"), test_dir=Path("."), root_path=Path("."))

def test_config_invalid_extension(tmp_path):
    """Verify that only .py files are accepted."""
    wrong_file = tmp_path / "data.txt"
    wrong_file.write_text("not code")
    with pytest.raises(ValueError, match="extension '.py'"):
        Config(original_file_path=wrong_file, test_dir=tmp_path, root_path=tmp_path)

def test_config_root_path_mismatch(tmp_path):
    """Verify that project root must contain the source file."""
    root1 = tmp_path / "root1"
    root1.mkdir()
    root2 = tmp_path / "root2"
    root2.mkdir()
    f = root1 / "logic.py"
    f.write_text("x = 1")
    
    config = Config(original_file_path=f, test_dir=root1, root_path=root2)
    from pymutator.runner import run_tests, Status
    with pytest.raises(ValueError):
        run_tests("x = 2", config)