"""LTL to GNBA conversion."""

from dataclasses import dataclass

from src.automata.closure import (
    TRUE_ATOM,
    compute_closure,
    compute_elementary_sets,
    rewrite,
)
from src.parser.ast_nodes import (
    ASTNode,
    Atom,
    Next,
    Until,
)


@dataclass
class GNBA:
    """Generalized Non-deterministic Buchi Automaton."""

    states: list[frozenset[str]]
    initial_states: list[frozenset[str]]
    # One frozenset[frozenset[str]] per Until subformula in closure
    acceptance_sets: list[frozenset[frozenset[str]]]
    transitions: dict[int, dict[frozenset[str], list[int]]]
    atomic_props: frozenset[str]


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

        # Only the matching AP set is stored. Callers must use
        # transitions[i].get(A, []) for other AP subsets,
        # which implicitly have no successors.
        transitions[i] = {b_ap: successors}

    return transitions


def ltl_to_gnba(formula: ASTNode) -> GNBA:
    """Convert an LTL formula to a GNBA.

    Args:
        formula: LTL formula as ASTNode.

    Returns:
        GNBA representing the formula.
    """
    # Rewrite to basic operators (And, Not, Next, Until)
    phi = rewrite(formula)

    # Compute closure (subformulas + their negations)
    closure = compute_closure(phi)

    # Compute maximally consistent subsets
    states = compute_elementary_sets(closure)

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
        if isinstance(node, Atom) and node.name != TRUE_ATOM.name
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
