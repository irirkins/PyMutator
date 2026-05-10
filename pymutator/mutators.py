import libcst as cst
from libcst.metadata import PositionProvider
from abc import ABC, abstractmethod
from typing import Dict, List


mutation_types = (
    cst.BinaryOperation,
    cst.ComparisonTarget,
    cst.BooleanOperation,
    cst.Integer,
    cst.Name,
    cst.SimpleString
)


class Helper(ABC):
    """Abstract base class for node mutations."""

    @classmethod
    @abstractmethod
    def get_rules(cls) -> Dict:
        """Class method to access rules without instantiation."""
        pass

    @property
    def rules(self) -> Dict:
        """
        Rules which define how to mutate the node.
        Property to access rules from an instance.
        """
        return self.get_rules()

    def __init__(self, node: cst.CSTNode) -> None:
        self.node = node

    def mutate(self) -> cst.CSTNode:
        """Mutate the node operator based on defined rules."""
        type_op = type(self.node.operator)
        new_operator = self.rules.get(type_op, type_op)()
        return self.node.with_changes(operator=new_operator)


class Arithmetic(Helper):
    """Class for arithmetic mutations (e.g., + to -, * to /)."""

    @classmethod
    def get_rules(cls) -> Dict:
        return {
            cst.Add: cst.Subtract,
            cst.Subtract: cst.Add,
            cst.BitAnd: cst.BitOr,
            cst.BitOr: cst.BitAnd,
            cst.Divide: cst.FloorDivide,
            cst.FloorDivide: cst.Divide,
            cst.Modulo: cst.Divide,
            cst.LeftShift: cst.RightShift,
            cst.RightShift: cst.LeftShift,
            cst.Multiply: cst.Add,
            cst.Power: cst.Multiply,
        }


class Compare(Helper):
    """Class for mutations of comparison operations."""

    @classmethod
    def get_rules(cls) -> Dict:
        return {
            cst.GreaterThan: cst.GreaterThanEqual,
            cst.GreaterThanEqual: cst.GreaterThan,
            cst.LessThan: cst.LessThanEqual,
            cst.LessThanEqual: cst.LessThan,
            cst.Equal: cst.Is,
            cst.Is: cst.Equal,
            cst.In: cst.Is,
        }


class Constants(Helper):
    """
    Class which mutates constants:
        - add 1 to integer
        - string to empty string
        - True <-> False
    """

    @classmethod
    def get_rules(cls) -> Dict:
        return {}

    def mutate(self) -> cst.CSTNode:
        node = self.node
        if isinstance(node, cst.Integer):
            return node.with_changes(value=str(int(node.value) + 1))
        
        if isinstance(node, cst.Name) and node.value in ["True", "False"]:
            new_val = "False" if node.value == "True" else "True"
            return node.with_changes(value=new_val)
        
        if isinstance(node, cst.SimpleString):
            return node.with_changes(value="''")
            
        return node


class BoolOp(Helper):
    """Class for mutations of boolean operations (and/or)."""

    @classmethod
    def get_rules(cls) -> Dict:
        return{
            cst.And: cst.Or,
            cst.Or: cst.And
        }


helpers = {
    cst.BinaryOperation: Arithmetic,
    cst.ComparisonTarget: Compare,
    cst.BooleanOperation: BoolOp,
    cst.Integer: Constants,
    cst.Name: Constants,
    cst.SimpleString: Constants
}


def is_good_type(node: cst.CSTNode, enabled_mutations: List[str]) -> bool:
    """Check should the node be mutated or not."""

    node_type = type(node)
    if node_type not in helpers:
        return False

    if enabled_mutations is not None:
        if helpers[node_type].__name__ not in enabled_mutations:
            return False

    if not isinstance(node, mutation_types):
        return False

    if isinstance(node, (cst.BinaryOperation, cst.ComparisonTarget, cst.BooleanOperation)):
        helper_class = helpers[node_type]
        return type(node.operator) in helper_class.get_rules()

    if isinstance(node, cst.Name):
        return node.value in ["True", "False"]

    return True


comment_types = (
    cst.SimpleStatementLine, 
    cst.If, 
    cst.For, 
    cst.While, 
    cst.FunctionDef, 
    cst.ClassDef
)


def has_no_mutation(node: cst.CSTNode) -> bool:
    return isinstance(node, comment_types) and \
           hasattr(node, "trailing_whitespace") and \
           node.trailing_whitespace.comment is not None and \
           "# no mutation" in node.trailing_whitespace.comment.value


class Visitor(cst.CSTVisitor):
    """Class for visiting nodes, collecting metadata and counting "good" nodes."""

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, enabled_mutations: List[str]) -> None:
        super().__init__()
        self.counter = 0
        self.all_mutations = {}
        self.skip = False
        self.enabled_mutations = enabled_mutations


    def catch_no_mutate(self, node: cst.CSTNode) -> None:
        if has_no_mutation(node):
            self.skip = True

    def node_leave(self, node: cst.CSTNode) -> None:
        if is_good_type(node, self.enabled_mutations) and not self.skip:
            self.counter += 1
            line_num = self.get_metadata(PositionProvider, node).start.line
            self.all_mutations[self.counter] = line_num

    def line_leave(self, node: cst.CSTNode) -> None:
        if has_no_mutation(node):
            self.skip = False


for node_type in mutation_types:
    leave_name = f"leave_{node_type.__name__}"
    setattr(Visitor, leave_name, Visitor.node_leave)


class Transformer(cst.CSTTransformer):
    """Main transformer that applies exactly one mutation per pass."""

    def __init__(self, target: int, enabled_mutations: List[str] = None) -> None:
        super().__init__()
        self.counter = 0
        self.target = target
        self.skip = False
        self.enabled_mutations = enabled_mutations

    def line_visit(self, node: cst.CSTNode) -> bool:
        if has_no_mutation(node):
            self.skip = True

        return True
    
    def line_leave(self, old_node: cst.CSTNode, new_node: cst.CSTNode) -> cst.CSTNode:
        if has_no_mutation(old_node):
            self.skip = False
        return new_node

    def mutate_node(self, old_node: cst.CSTNode, new_node: cst.CSTNode) -> cst.CSTNode:
        """Generic handler for node mutation logic."""

        if is_good_type(old_node, self.enabled_mutations) and not self.skip:
            self.counter += 1

            if self.counter == self.target:
                mutator = helpers[type(old_node)](new_node)
                return mutator.mutate()

        return new_node


for node_type in mutation_types:
    leave_name = f"leave_{node_type.__name__}"
    setattr(Transformer, leave_name, Transformer.mutate_node)


for node_type in comment_types:
    leave_name = f"leave_{node_type.__name__}"
    visit_name = f"visit_{node_type.__name__}"
    setattr(Visitor, visit_name, Visitor.catch_no_mutate)
    setattr(Transformer, visit_name, Transformer.line_visit)
    setattr(Visitor, leave_name, Visitor.line_leave)
    setattr(Transformer, leave_name, Transformer.line_leave)