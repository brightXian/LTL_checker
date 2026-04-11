"""GNBA to NBA conversion."""

from dataclasses import dataclass

from src.automata.gnba import GNBA

# Type alias for transitions map
_TransitionMap = dict[tuple[int, int], dict[frozenset[str], list[tuple[int, int]]]]


@dataclass
class NBA:
    """Non-deterministic Buchi Automaton."""

    states: list[tuple[int, int]]
    initial_states: list[tuple[int, int]]
    acceptance_set: frozenset[tuple[int, int]]
    transitions: _TransitionMap
    atomic_props: frozenset[str]

    def _state_str(self, state: tuple) -> str:
        q, layer = state
        return f"q{q}_{layer}"

    def __str__(self) -> str:
        lines = ["[NBA]"]
        lines.append(f"  AP: {{{', '.join(sorted(self.atomic_props))}}}")
        lines.append("  States:")
        for state in self.states:
            marker = "*" if state in self.initial_states else " "
            lines.append(f"    {marker} {self._state_str(state)}")
        lines.append("  Acceptance set:")
        acc_str = ", ".join(self._state_str(s) for s in sorted(self.acceptance_set))
        lines.append(f"      F = {{{acc_str}}}")
        lines.append("  Transitions:")
        for state, trans in self.transitions.items():
            for ap_set, succs in trans.items():
                if succs:
                    ap_str = ", ".join(sorted(ap_set)) if ap_set else "∅"
                    succ_str = ", ".join(self._state_str(s) for s in succs)
                    lines.append(
                        f"      {self._state_str(state)} -> {{{succ_str}}}  [{ap_str}]"
                    )
        return "\n".join(lines)


def gnba_to_nba(gnba: GNBA, verbose: bool = False) -> NBA:
    """Convert GNBA to NBA.

    Args:
        gnba: The Generalized Non-deterministic Buchi Automaton.

    Returns:
        NBA representing the same language.
    """
    k = len(gnba.acceptance_sets)
    num_states = len(gnba.states)

    # Find initial state indices in gnba.states (used in both branches)
    initial_indices = [gnba.states.index(init) for init in gnba.initial_states]

    # Special case: k == 0
    # Every infinite run is accepting
    if k == 0:
        states = [(q, 1) for q in range(num_states)]
        initial_states = [(q, 1) for q in initial_indices]
        # All states are accepting
        acceptance_set = frozenset(states)
    else:
        states = [(q, i) for q in range(num_states) for i in range(1, k + 1)]
        initial_states = [(q, 1) for q in initial_indices]
        # Acceptance set F': {(q, 1) | gnba.states[q] in gnba.acceptance_sets[0]}
        f0 = gnba.acceptance_sets[0]
        acceptance_set = frozenset(
            (q, 1) for q in range(num_states) if gnba.states[q] in f0
        )

    # Build transitions
    transitions: _TransitionMap = {}
    if k == 0:
        for q in range(num_states):
            for ap_set, succ_list in gnba.transitions[q].items():
                new_succs = [(s, 1) for s in succ_list]
                transitions[(q, 1)] = {ap_set: new_succs}
    else:
        for q in range(num_states):
            for i in range(1, k + 1):
                for ap_set, succ_list in gnba.transitions[q].items():
                    fi = gnba.acceptance_sets[i - 1]
                    # Check if current state is in acceptance set fi
                    if gnba.states[q] not in fi:
                        # Stay in same layer
                        result = [(s, i) for s in succ_list]
                    else:
                        # Move to next layer
                        next_layer = (i % k) + 1
                        result = [(s, next_layer) for s in succ_list]

                    transitions[(q, i)] = {ap_set: result}

    nba = NBA(
        states=states,
        initial_states=initial_states,
        acceptance_set=acceptance_set,
        transitions=transitions,
        atomic_props=gnba.atomic_props,
    )

    if verbose:
        print(nba)
    return nba
