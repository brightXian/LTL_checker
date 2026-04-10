"""LTL to GNBA conversion."""

from dataclasses import dataclass
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


@dataclass
class GNBA:
    """Generalized Non-deterministic Buchi Automaton."""

    states: list[frozenset[str]]
    initial_states: list[frozenset[str]]
    # One frozenset[frozenset[str]] per Until subformula in closure
    acceptance_sets: list[frozenset[frozenset[str]]]
    transitions: dict[int, dict[frozenset[str], list[int]]]
    atomic_props: frozenset[str]


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


def _build_transitions(
    states: list[frozenset[str]],
    closure: list[ASTNode],
    ap_names: frozenset[str],
) -> dict[int, dict[frozenset[str], list[int]]]:
    """Build transition relation for GNBA.

    For each state B and each A subset of AP:
    - If A != B ∩ AP: no successors
    - Otherwise: find B' satisfying consistency conditions

    Args:
        states: List of elementary sets.
        closure: Closure of the formula.
        ap_names: Set of atomic proposition names.

    Returns:
        Transition dict.
    """
    transitions: dict[int, dict[frozenset[str], list[int]]] = {}

    # Precompute Next and Until formulas in closure
    next_formulas: list[tuple[str, str]] = []
    until_formulas: list[tuple[str, str, str]] = []

    for psi in closure:
        if isinstance(psi, Next):
            next_formulas.append((str(psi), str(psi.child)))
        elif isinstance(psi, Until):
            until_formulas.append((str(psi), str(psi.left), str(psi.right)))

    for i, b in enumerate(states):
        # Get atomic propositions true in b
        b_ap = b & ap_names

        # Find successors b_prime that satisfy consistency
        successors: list[int] = []

        for j, b_prime in enumerate(states):
            valid = True

            # Next-consistency
            for next_key, child_key in next_formulas:
                if next_key in b:
                    if child_key not in b_prime:
                        valid = False
                        break
                else:
                    if child_key in b_prime:
                        valid = False
                        break

            if not valid:
                continue

            # Until-consistency
            for until_key, left_key, right_key in until_formulas:
                # Until in b iff (b in b or (a in b and Until in b'))
                if until_key in b:
                    if right_key not in b and (
                        left_key not in b or until_key not in b_prime
                    ):
                        valid = False
                        break
                else:
                    if left_key in b and until_key in b_prime:
                        valid = False
                        break

            if valid:
                successors.append(j)

        transitions[i] = {b_ap: successors}
        # Only the matching AP set is stored. Callers must use
        # transitions[i].get(A, []) for other AP subsets,
        # which implicitly have no successors.

    return transitions


def ltl_to_gnba(formula: ASTNode) -> GNBA:
    """Convert an LTL formula to a GNBA.

    Args:
        formula: LTL formula as ASTNode.

    Returns:
        GNBA representing the formula.
    """
    # Rewrite to basic operators (And, Not, Next, Until)
    phi = _rewrite(formula)

    # Compute closure (subformulas + their negations)
    closure = _compute_closure(phi)

    # Compute maximally consistent subsets
    states = _compute_elementary_sets(closure)

    # Initial states: {b in states | phi in b}
    initial_states = [b for b in states if str(phi) in b]

    # Acceptance sets: for each Until in closure
    acceptance_sets: list[frozenset[frozenset[str]]] = []
    for psi in closure:
        if isinstance(psi, Until):
            until_key = str(psi)
            right_key = str(psi.right)
            acc = frozenset(b for b in states if until_key not in b or right_key in b)
            acceptance_sets.append(acc)

    # Atomic propositions (excluding TRUE_ATOM)
    ap_names = frozenset(
        node.name
        for node in closure
        if isinstance(node, Atom) and node.name != "__true__"
    )

    # Transitions
    transitions = _build_transitions(states, closure, ap_names)

    return GNBA(
        states=states,
        initial_states=initial_states,
        acceptance_sets=acceptance_sets,
        transitions=transitions,
        atomic_props=ap_names,
    )
