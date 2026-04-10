"""Closure computation for LTL formulas."""

from itertools import combinations

from src.parser.ast_nodes import (
    And,
    ASTNode,
    Atom,
    BinaryNode,
    Finally,
    Globally,
    Imply,
    Next,
    Not,
    Or,
    UnaryNode,
    Until,
)

# Sentinel for always-true proposition
TRUE_ATOM = Atom("__true__")


def _negate(node: ASTNode) -> ASTNode:
    """Return the negation of a node, simplifying double negation."""
    if isinstance(node, Not):
        return node.child
    return Not(child=node)


def _rewrite(formula: ASTNode) -> ASTNode:
    """Rewrite formula to basic operators (Atom, Not, And, Next,Until only).

    Rules:
      Or(a, b)     -> Not(And(Not(a), Not(b)))
      Imply(a, b)  -> Not(And(a, Not(b)))
      Finally(a)   -> Until(TRUE_ATOM, a)
      Globally(a)  -> Not(Until(TRUE_ATOM, Not(a)))
      Not(Not(x))  -> x (simplify double negation)

    Args:
        formula: Original LTL formula.

    Returns:
        Rewritten formula with only basic operators.
    """
    if isinstance(formula, Atom):
        return formula

    if isinstance(formula, Not):
        return _negate(_rewrite(formula.child))

    if isinstance(formula, And):
        return And(left=_rewrite(formula.left), right=_rewrite(formula.right))

    if isinstance(formula, Or):
        # Or(a, b) -> Not(And(Not(a), Not(b)))
        not_a = _negate(_rewrite(formula.left))
        not_b = _negate(_rewrite(formula.right))
        and_node = And(left=not_a, right=not_b)
        return Not(child=and_node)

    if isinstance(formula, Imply):
        # Imply(a, b) -> Not(And(a, Not(b)))
        a = _rewrite(formula.left)
        b = _negate(_rewrite(formula.right))
        and_node = And(left=a, right=b)
        return Not(child=and_node)

    if isinstance(formula, Next):
        return Next(child=_rewrite(formula.child))

    if isinstance(formula, Finally):
        # Finally(a) -> Until(TRUE_ATOM, a)
        return Until(left=TRUE_ATOM, right=_rewrite(formula.child))

    if isinstance(formula, Globally):
        # Globally(a) -> Not(Until(TRUE_ATOM, Not(a)))
        a = _rewrite(formula.child)
        return _negate(Until(left=TRUE_ATOM, right=_negate(a)))

    if isinstance(formula, Until):
        return Until(left=_rewrite(formula.left), right=_rewrite(formula.right))

    # Reject unknown node types
    raise TypeError(f"Unexpected AST node type: {type(formula)}")


def _collect_subformulas(node: ASTNode) -> list[ASTNode]:
    """Collect all subformulas of a node recursively."""
    result: list[ASTNode] = [node]
    if isinstance(node, UnaryNode):
        result.extend(_collect_subformulas(node.child))
    elif isinstance(node, BinaryNode):
        result.extend(_collect_subformulas(node.left))
        result.extend(_collect_subformulas(node.right))
    return result


def _compute_closure(formula: ASTNode) -> list[ASTNode]:
    """Compute closure of formula.

    Closure(phi) = all subformulas psi of phi plus their negations Not(psi).
    Not(Not(x)) is simplified to x when adding negations.

    Args:
        formula: A formula already rewritten by _rewrite().

    Returns:
        List of all formulas in the closure.
    """
    subformulas = _collect_subformulas(formula)

    closure: list[ASTNode] = []
    seen: set[str] = set()

    # Add subformulas and their negations
    for psi in subformulas:
        key = str(psi)
        if key not in seen:
            closure.append(psi)
            seen.add(key)

        neg = _negate(psi)
        neg_key = str(neg)
        if neg_key not in seen:
            closure.append(neg)
            seen.add(neg_key)

    return closure


def _is_elementary(b: frozenset[str], closure: list[ASTNode]) -> bool:
    """Check if b is an elementary set.

    Args:
        b: Set of formulas (as strings) in the candidate set.
        closure: Precomputed closure of the formula.

    Returns:
        True if b satisfies all elementary conditions.
    """
    # And-consistency
    for psi in closure:
        if isinstance(psi, And):
            and_key = str(psi)
            left_key = str(psi.left)
            right_key = str(psi.right)
            if and_key in b:
                if left_key not in b or right_key not in b:
                    return False
            else:
                if left_key in b and right_key in b:
                    return False

    # Both negation-consistency and maximality: exactly one of
    # {psi, neg(psi)} must be in b
    for psi in closure:
        psi_str = str(psi)
        neg_str = str(_negate(psi))
        if psi_str in b and neg_str in b:
            return False
        if psi_str not in b and neg_str not in b:
            return False

    # TRUE_ATOM check
    true_str = str(TRUE_ATOM)
    if any(str(psi) == true_str for psi in closure) and true_str not in b:
        return False

    # Until-consistency
    for psi in closure:
        if isinstance(psi, Until):
            until_key = str(psi)
            left_key = str(psi.left)
            right_key = str(psi.right)

            if right_key in b and until_key not in b:
                return False

            if until_key in b and right_key not in b and left_key not in b:
                return False

    return True


def _compute_elementary_sets(closure: list[ASTNode]) -> list[frozenset[str]]:
    """Compute all elementary sets using powerset enumeration.

    Args:
        closure: Precomputed closure of the formula.

    Returns:
        List of all elementary sets.
    """
    # Get all formula strings in closure
    formula_strs = [str(psi) for psi in closure]

    elementary: list[frozenset[str]] = []

    # Enumerate all 2^n subsets using powerset
    for r in range(len(formula_strs) + 1):
        for combo in combinations(formula_strs, r):
            b = frozenset(combo)
            if _is_elementary(b, closure):
                elementary.append(b)

    return elementary
