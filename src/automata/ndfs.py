from dataclasses import dataclass

from src.automata.product import ProductTS


@dataclass
class NDFSResult:
    satisfied: bool
    counterexample: list[tuple] | None  # None if satisfied


def cycle_check(s: tuple, product: ProductTS, t: set, v: list) -> bool:
    """Inner DFS to check if there's an accepting cycle reachable from s.

    t and v are passed as parameters and modified in place.
    """
    # Push s to v, add to t
    v.append(s)
    t.add(s)

    cycle_found = False
    while v and not cycle_found:
        s_prime = v[-1]
        # Check for backward edge to s (cycle found)
        if s in product.transitions.get(s_prime, []):
            v.append(s)
            cycle_found = True
            break

        # Find unvisited successor
        successors = product.transitions.get(s_prime, [])
        found_unvisited = False
        for s_double_prime in successors:
            if s_double_prime not in t:
                v.append(s_double_prime)
                t.add(s_double_prime)
                found_unvisited = True
                break

        if not found_unvisited:
            v.pop()

    return cycle_found


def reachable_cycle(
    s: tuple, product: ProductTS, r: set, u: list, t: set, v: list
) -> bool:
    """Outer DFS to find if there's an accepting cycle from s."""
    # Push s to u, add to r
    u.append(s)
    r.add(s)

    cycle_found = False
    while u and not cycle_found:
        s_prime = u[-1]

        # Find unvisited successor
        successors = product.transitions.get(s_prime, [])
        found_unvisited = False
        for s_double_prime in successors:
            if s_double_prime not in r:
                u.append(s_double_prime)
                r.add(s_double_prime)
                found_unvisited = True
                break

        if not found_unvisited:
            u.pop()
            # After all successors explored, check for accepting cycle
            if s_prime in product.accepting_states and cycle_check(
                s_prime, product, t, v
            ):
                return True

    return cycle_found


def check_persistence(product: ProductTS) -> NDFSResult:
    """Check whether the product TS satisfies the persistence property.

    Args:
        product: Product of TS and NBA.

    Returns:
        NDFSResult with satisfied=True if no accepting cycle exists,
        otherwise satisfied=False with a counterexample path.
    """
    # Local state for NDFS algorithm
    r: set = set()  # states visited by outer DFS
    u: list = []  # outer DFS stack (path to current state)
    t: set = set()  # states visited by inner DFS, SHARED across all inner calls
    v: list = []  # inner DFS stack

    # Start from each initial state
    for init in product.initial_states:
        if init not in r and reachable_cycle(init, product, r, u, t, v):
            # Build counterexample: u + v
            counterexample = u + v
            return NDFSResult(satisfied=False, counterexample=counterexample)

    # No cycle found
    return NDFSResult(satisfied=True, counterexample=None)
