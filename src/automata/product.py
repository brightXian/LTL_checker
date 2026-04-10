"""Product of Transition System and NBA."""

from collections import deque
from dataclasses import dataclass

from src.automata.nba import NBA


@dataclass
class ProductTS:
    """Product automaton of TS and NBA."""

    states: list[tuple]
    initial_states: list[tuple]
    transitions: dict[tuple, list[tuple]]
    accepting_states: frozenset[tuple]


def product_ts_nba(ts, nba: NBA) -> ProductTS:
    """Build product of Transition System and NBA.

    Args:
        ts: Transition System with attributes initial_states, successors, label.
        nba: Non-deterministic Buchi Automaton.

    Returns:
        ProductTS with reachable states and transitions.
    """
    # Compute initial states: for each TS initial state,
    # follow NBA transitions using TS state label
    initial_candidates = []

    for s in ts.initial_states:
        label = ts.label(s)
        for q in nba.initial_states:
            nba_succs = nba.transitions.get(q, {}).get(label, [])
            for nba_state in nba_succs:
                initial_candidates.append((s, nba_state))

    # Order-preserving dedup
    seen = set()
    initial_states = []
    for item in initial_candidates:
        if item not in seen:
            seen.add(item)
            initial_states.append(item)

    # BFS to find reachable states and build transitions
    reachable: set[tuple] = set()
    transitions: dict[tuple, list[tuple]] = {}

    queue = deque(initial_states)
    for state in initial_states:
        reachable.add(state)

    while queue:
        s, q = queue.popleft()

        # Get TS successors of current state
        ts_succs = ts.successors(s)

        current_transitions = []

        for t in ts_succs:
            # Read label of destination state t
            label = ts.label(t)

            # Follow NBA transitions using the label
            nba_succs = nba.transitions.get(q, {}).get(label, [])

            for nba_state in nba_succs:
                product_state = (t, nba_state)
                current_transitions.append(product_state)

                if product_state not in reachable:
                    reachable.add(product_state)
                    queue.append(product_state)

        transitions[(s, q)] = current_transitions

    # Build final state lists
    states = list(reachable)

    # Determine accepting states (NBA component in acceptance set)
    accepting_states = frozenset(
        (s, q) for (s, q) in reachable if q in nba.acceptance_set
    )

    return ProductTS(
        states=states,
        initial_states=initial_states,
        transitions=transitions,
        accepting_states=accepting_states,
    )
