from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from enum import Enum
from typing import List, Optional


class Status(Enum):
    """
    Enumeration of possible mutant statuses.
    
    KILLED - mutant failed tests (good result)
    SURVIVED - mutant passed tests (test suite is weak)
    TIMEOUT - execution time exceeded (possible infinite loop)
    """

    KILLED = 0
    SURVIVED = 1
    TIMEOUT = 2


@dataclass(frozen=True)
class MutationResult:
    """Data class to store the result of a single mutation test."""

    number: int
    line: int
    status: Status
    diff: str = ""


class Config(BaseModel):
    """Configuration model for PyMutator settings."""

    original_file_path: Path
    test_dir: Path
    root_path: Path
    timeout: int = Field(default=5, gt=0)
    mutant_cnt: int = Field(default=10, ge=0)
    jobs: int = Field(default=1, ge=1)
    full_report: bool = Field(default=False)
    enabled_mutations: Optional[List[str]] = Field(default=None)

    @field_validator("original_file_path")
    @classmethod
    def check_file_exists(cls, v: Path) -> Path:
        """Verify that the source file exists and is a valid .py file."""
        if not v.exists():
            raise ValueError(f"File not found: {v}")
        if not v.is_file():
            raise ValueError(f"Not a file: {v}")
        if v.suffix != ".py":
            raise ValueError(f"File must have extension '.py': {v}")
        return v

    @field_validator("test_dir")
    @classmethod
    def check_dir_exists(cls, v: Path) -> Path:
        """Verify that the test directory exists and is a directory."""
        if not v.exists() or not v.is_dir():
            raise ValueError(f"Test directory is not found: {v}")
        return v

    @field_validator("root_path")
    @classmethod
    def check_root_exists(cls, v: Path) -> Path:
        """Verify that the root directory exists and is a directory."""
        if not v.exists() or not v.is_dir():
            raise ValueError(f"Root directory is not found: {v}")
        return v

    @field_validator("enabled_mutations")
    @classmethod
    def check_mutator_names(cls, v: List[str]) -> List[str]:
        allowed = {"Arithmetic", "Compare", "Constants", "BoolOp"}
        if v is not None:
            for name in v:
                if name not in allowed:
                    raise ValueError(
                        f"Invalid mutator name: '{name}'. "
                        f"Available options: {', '.join(allowed)}"
                    )
        return v
