import pytest
import libcst as cst
from pymutator.mutators import Transformer, Visitor, is_good_type

@pytest.mark.parametrize("original, target, expected", [
    ("a + b", 1, "a - b"),
    ("a - b", 1, "a + b"),
    ("a * b", 1, "a + b"),
    ("a / b", 1, "a // b"),
    ("a // b", 1, "a / b"),
    ("a % b", 1, "a / b"),
    ("a ** b", 1, "a * b"),
    ("a & b", 1, "a | b"),
    ("a | b", 1, "a & b"),
    ("a << b", 1, "a >> b"),
    ("a >> b", 1, "a << b"),
    ("a == b", 1, "a is b"),
    ("a > b", 1, "a >= b"),
    ("a < b", 1, "a <= b"),
    ("a >= b", 1, "a > b"),
    ("a <= b", 1, "a < b"),
    ("a is b", 1, "a == b"),
    ("a in b", 1, "a is b"),
    ("a and b", 1, "a or b"),
    ("a or b", 1, "a and b"),
    ("10", 1, "11"),
    ("True", 1, "False"),
    ("False", 1, "True"),
    ("'hello'", 1, "''"),
])
def test_all_rules_from_code(original, target, expected):
    tree = cst.parse_module(original)
    wrapper = cst.MetadataWrapper(tree)
    transformer = Transformer(target=target)
    mutated_tree = wrapper.visit(transformer)
    assert mutated_tree.code.strip() == expected

def test_bitxor_is_ignored():
    """Verify that BitXor is not counted as a mutation point."""
    code = "a ^ b"
    tree = cst.parse_module(code)
    visitor = Visitor(enabled_mutations=None)
    cst.MetadataWrapper(tree).visit(visitor)
    assert visitor.counter == 0

@pytest.mark.parametrize("code, expected_count", [
    ("for i in range(10): # no mutation\n    x = i + 1", 2),
    ("def func(a, b): # no mutation\n    return a + b", 1),
    ("while True: # no mutation\n    pass", 0),
    ("class A: # no mutation\n    x = 1", 1),
])
def test_no_mutation_on_complex_structures(code, expected_count):
    """Verify # no mutation works on different statement headers."""
    tree = cst.parse_module(code)
    visitor = Visitor(enabled_mutations=None)
    cst.MetadataWrapper(tree).visit(visitor)
    assert visitor.counter == expected_count

def test_is_good_type_logic():
    from pymutator.mutators import is_good_type
    node_add = cst.BinaryOperation(left=cst.Name("a"), operator=cst.Add(), right=cst.Name("b"))
    assert is_good_type(node_add, None) is True
    assert is_good_type(cst.Name("a"), None) is False
    assert is_good_type(cst.Name("True"), None) is True