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

    def __str__(self) -> str:
        lines = ["[Product TS x NBA]"]
        lines.append("  States:")
        for s, q in self.states:
            q_idx, layer = q
            marker = "*" if (s, q) in self.initial_states else " "
            lines.append(f"    {marker} (s{s}, q{q_idx}_{layer})")
        lines.append("  Acceptance set:")
        acc_str = ", ".join(
            f"(s{s}, q{q_idx}_{layer})"
            for s, (q_idx, layer) in sorted(self.accepting_states)
        )
        lines.append(f"      F = {{{acc_str}}}")
        lines.append("  Transitions:")
        for (s, q), succs in self.transitions.items():
            if succs:
                q_idx, layer = q
                succ_str = ", ".join(
                    f"(s{t}, q{p_idx}_{p_layer})" for t, (p_idx, p_layer) in succs
                )
                lines.append(f"      (s{s}, q{q_idx}_{layer}) -> {{{succ_str}}}")
        return "\n".join(lines)


def product_ts_nba(ts, nba: NBA, verbose: bool = False) -> ProductTS:
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
        label = ts.label(s) & nba.atomic_props
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
            label = ts.label(t) & nba.atomic_props

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

    product = ProductTS(
        states=states,
        initial_states=initial_states,
        transitions=transitions,
        accepting_states=accepting_states,
    )

    if verbose:
        print(product)
    return product
