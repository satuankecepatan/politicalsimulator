"""Safe AST-based precondition expression evaluator (no raw eval)."""

from __future__ import annotations

import ast
import operator
from typing import Any

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, context: dict[str, Any]):
        self.context = context

    def eval(self, expr_str: str) -> bool:
        if not expr_str or not expr_str.strip():
            return True
        try:
            tree = ast.parse(expr_str.strip(), mode="eval")
            return bool(self.visit(tree.body))
        except Exception:
            return False

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.context:
            return self.context[node.id]
        if node.id in {"True", "true"}:
            return True
        if node.id in {"False", "false"}:
            return False
        return None

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        val = self.visit(node.value)
        if val is None:
            return None
        if isinstance(val, dict):
            return val.get(node.attr)
        return getattr(val, node.attr, None)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op_type = type(node.op)
        operand = self.visit(node.operand)
        if op_type is ast.Not:
            return not operand
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            left = self.visit(node.left)
            right = self.visit(node.right)
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        if isinstance(node.op, ast.And):
            for val in node.values:
                if not self.visit(val):
                    return False
            return True
        elif isinstance(node.op, ast.Or):
            for val in node.values:
                if self.visit(val):
                    return True
            return False
        return False

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            op_type = type(op)
            right = self.visit(comparator)
            if op_type in SAFE_OPERATORS:
                if not SAFE_OPERATORS[op_type](left, right):
                    return False
                left = right
            else:
                return False
        return True

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Disallowed AST expression node: {type(node).__name__}")


def evaluate_precondition(expr: str | None, context: dict[str, Any]) -> bool:
    """Safely evaluate precondition boolean expression against simulation context."""
    if not expr:
        return True
    return SafeEvaluator(context).eval(expr)
