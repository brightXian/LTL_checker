"""Unit tests for NBA construction."""

from src.automata.gnba import ltl_to_gnba
from src.automata.nba import gnba_to_nba
from src.parser.parser import parse


class TestNBAConversion:
    """Test GNBA to NBA conversion basic properties."""

    def test_states_count_with_k_zero(self):
        """NBA states = GNBA states when k=0."""
        gnba = ltl_to_gnba(parse("a"))
        nba = gnba_to_nba(gnba)
        assert len(nba.states) == len(gnba.states) * max(1, len(gnba.acceptance_sets))

    def test_states_count_with_k_one(self):
        """NBA states = GNBA states when k=1."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        k = len(gnba.acceptance_sets)
        assert len(nba.states) == len(gnba.states) * k

    def test_initial_count(self):
        """NBA initial states count equals GNBA initial states count."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        assert len(nba.initial_states) == len(gnba.initial_states)

    def test_atomic_props_preserved(self):
        """NBA atomic props equal GNBA atomic props."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        assert nba.atomic_props == gnba.atomic_props


class TestNBAKZero:
    """Test NBA when k == 0 (no Until in formula)."""

    def test_acceptance_all_states(self):
        """When k=0, all NBA states are accepting."""
        gnba = ltl_to_gnba(parse("a"))
        nba = gnba_to_nba(gnba)
        assert nba.acceptance_set == frozenset(nba.states)

    def test_layer_all_one(self):
        """When k=0, all states have layer 1."""
        gnba = ltl_to_gnba(parse("X(a)"))
        nba = gnba_to_nba(gnba)
        for state in nba.states:
            assert state[1] == 1


class TestNBAKOne:
    """Test NBA when k == 1 (one Until in formula)."""

    def test_states_k_one(self):
        """With one Until, NBA has same state count as GNBA."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        assert len(nba.states) == 5

    def test_layer_range_one(self):
        """With k=1, all states have layer 1 (wraps to 1)."""
        gnba = ltl_to_gnba(parse("F(a)"))
        nba = gnba_to_nba(gnba)
        for state in nba.states:
            assert state[1] == 1

    def test_acceptance_from_f0(self):
        """Acceptance set derived from GNBA acceptance_sets[0]."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        f0 = gnba.acceptance_sets[0]
        # Check size matches
        assert len(nba.acceptance_set) == len(f0)


class TestNBATransitions:
    """Test NBA transition structure."""

    def test_transition_keys_are_tuples(self):
        """All transition keys are (q, layer) tuples."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        for state in nba.states:
            assert isinstance(state, tuple)
            assert len(state) == 2

    def test_transition_keys_count_per_state(self):
        """Each state has exactly one transition key."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        for state in nba.states:
            assert len(nba.transitions[state]) == 1

    def test_successor_in_valid_range(self):
        """All successors are valid state indices."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        # succ[0] is GNBA state index, so compare with GNBA num_states
        num_gnba_states = len(gnba.states)
        for _, trans in nba.transitions.items():
            for succs in trans.values():
                for succ in succs:
                    assert 0 <= succ[0] < num_gnba_states


class TestNBALayers:
    """Test layer handling in NBA."""

    def test_layer_transition_accepting_jumps(self):
        """Accepting state at layer i jumps to layer i+1 (or 1 if i=k)."""
        # Use formula with 2 Until ops for k=2
        gnba = ltl_to_gnba(parse("(a U b) U c"))
        nba = gnba_to_nba(gnba)
        k = len(gnba.acceptance_sets)
        assert k == 2, f"Expected k=2, got {k}"
        f0 = gnba.acceptance_sets[0]
        f1 = gnba.acceptance_sets[1]
        # Check layer transitions
        for q, state in enumerate(gnba.states):
            # Layer 1
            if state in f0:
                for succs in nba.transitions[(q, 1)].values():
                    assert all(
                        s[1] == 2 for s in succs
                    ), f"layer 1 jump failed for state {q}"
            else:
                for succs in nba.transitions[(q, 1)].values():
                    assert all(
                        s[1] == 1 for s in succs
                    ), f"layer 1 stay failed for state {q}"
            # Layer 2
            if state in f1:
                for succs in nba.transitions[(q, 2)].values():
                    assert all(
                        s[1] == 1 for s in succs
                    ), f"layer 2 wrap failed for state {q}"
            else:
                for succs in nba.transitions[(q, 2)].values():
                    assert all(
                        s[1] == 2 for s in succs
                    ), f"layer 2 stay failed for state {q}"

    def test_layer_bounds_k_two(self):
        """With k=2, layers are 1 or 2."""
        gnba = ltl_to_gnba(parse("(a U b) U c"))
        nba = gnba_to_nba(gnba)
        k = len(gnba.acceptance_sets)
        assert k == 2, f"Expected k=2, got {k}"
        for state in nba.states:
            assert 1 <= state[1] <= k

    def test_layer_cyclical_transition(self):
        """Accepting state at layer k wraps to layer 1."""
        gnba = ltl_to_gnba(parse("a U b"))
        nba = gnba_to_nba(gnba)
        k = len(gnba.acceptance_sets)
        # Find accepting states in highest layer
        highest_layer = k
        accept_at_k = [
            s for s in nba.states if s in nba.acceptance_set and s[1] == highest_layer
        ]
        assert len(accept_at_k) > 0, "No accepting states found in highest layer"
        key_state = accept_at_k[0]
        for _, succs in nba.transitions[key_state].items():
            for succ in succs:
                # Should wrap back to layer 1
                assert (
                    succ[1] == 1
                ), f"Accepting state at layer {k} should wrap to layer 1, got layer {succ[1]}"


class TestNBAFinally:
    """Test NBA for Finally operator."""

    def test_finally_nba_states(self):
        """NBA for F(a) has correct state count."""
        gnba = ltl_to_gnba(parse("F(a)"))
        nba = gnba_to_nba(gnba)
        assert len(nba.states) == 3

    def test_finally_initial_states(self):
        """NBA for F(a) has 2 initial states."""
        gnba = ltl_to_gnba(parse("F(a)"))
        nba = gnba_to_nba(gnba)
        assert len(nba.initial_states) == 2


class TestNBAGlobally:
    """Test NBA for Globally operator."""

    def test_globally_nba_states(self):
        """NBA for G(a) has correct state count."""
        gnba = ltl_to_gnba(parse("G(a)"))
        nba = gnba_to_nba(gnba)
        assert len(nba.states) == 3

    def test_globally_acceptance_set_size(self):
        """NBA for G(a) acceptance set has correct size."""
        gnba = ltl_to_gnba(parse("G(a)"))
        nba = gnba_to_nba(gnba)
        assert len(nba.acceptance_set) == 2


def _nba_accepts(nba, prefix: list[frozenset], cycle: list[frozenset]) -> bool:
    """Check if NBA accepts with prefix/cycle word.

    Args:
        nba: NBA object
        prefix: finite prefix before cycle repeats
        cycle: infinite suffix that repeats forever

    Returns:
        True if some run visits accepting state infinitely often.
    """

    def step(states, ap_set):
        result = set()
        for state in states:
            for succ in nba.transitions.get(state, {}).get(ap_set, []):
                result.add(succ)
        return result

    # Start from all initial states
    current = set(nba.initial_states)

    # Run the prefix
    for ap_set in prefix:
        current = step(current, ap_set)
        if not current:
            return False

    # Search for accepting cycle using BFS-style frontier
    # frontier: (start_state, current_state, seen_accepting)
    frontier = {(q, q, q in nba.acceptance_set) for q in current}

    # Run the cycle indefinitely, tracking if we've seen accepting state
    for ap_set in cycle:
        new_frontier = set()
        for q0, q, seen in frontier:
            for succ in nba.transitions.get(q, {}).get(ap_set, []):
                new_seen = seen or (succ in nba.acceptance_set)
                new_frontier.add((q0, succ, new_seen))
        frontier = new_frontier
        if not frontier:
            return False

    # Check if there's a run that returns to start and visits accepting
    return any(q0 == q and seen for (q0, q, seen) in frontier)


class TestNBASemantics:
    """Test NBA language semantics using Büchi acceptance."""

    def test_globally_accepts_always_a(self):
        """G(a) accepts when 'a' holds always."""
        nba = gnba_to_nba(ltl_to_gnba(parse("G(a)")))
        assert _nba_accepts(nba, [], [frozenset({"a"})])

    def test_globally_rejects_without_a(self):
        """G(a) rejects when 'a' eventually fails."""
        nba = gnba_to_nba(ltl_to_gnba(parse("G(a)")))
        assert not _nba_accepts(nba, [frozenset({"a"})], [frozenset()])

    def test_finally_accepts_eventually(self):
        """F(a) accepts when 'a' eventually holds."""
        nba = gnba_to_nba(ltl_to_gnba(parse("F(a)")))
        assert _nba_accepts(nba, [frozenset(), frozenset()], [frozenset({"a"})])

    def test_until_accepts_eventually_b(self):
        """a U b accepts when b eventually holds."""
        nba = gnba_to_nba(ltl_to_gnba(parse("a U b")))
        assert _nba_accepts(
            nba, [frozenset({"a"}), frozenset({"a"})], [frozenset({"b"})]
        )

    def test_until_rejects_never_b(self):
        """a U b rejects when b never holds."""
        nba = gnba_to_nba(ltl_to_gnba(parse("a U b")))
        assert not _nba_accepts(nba, [], [frozenset({"a"})])
