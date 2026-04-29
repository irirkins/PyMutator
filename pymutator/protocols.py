from typing import Protocol, Dict, runtime_checkable
import libcst as cst

@runtime_checkable
class MutatorHelper(Protocol):
    """Protocol defining the interface for all mutation helpers."""
    
    @classmethod
    def get_rules(cls) -> Dict:
        """Should return a mapping of original operators to mutated ones."""
        ...

    @property
    def rules(self) -> Dict:
        """Property to access rules from an instance."""
        ...

    def mutate(self) -> cst.CSTNode:
        """Should return a mutated version of the node."""
        ...
        