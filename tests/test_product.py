"""Unit tests for product automaton construction."""

from src.automata.nba import NBA
from src.automata.product import product_ts_nba


class MockTS:
    """Mock Transition System for testing."""

    def __init__(self, initial_states, successors_map, label_map):
        self.initial_states = initial_states
        self._successors = successors_map
        self._labels = label_map

    def successors(self, s):
        return self._successors.get(s, [])

    def label(self, s):
        return self._labels.get(s, frozenset())


class TestProductInitialStates:
    """Test product automaton initial states."""

    def test_initial_state_follows_nba_on_label(self):
        """Initial product state (s0, q) where q = delta(q0, L(s0))."""
        ts = MockTS(
            initial_states=[0],
            successors_map={0: [1], 1: []},
            label_map={0: frozenset({"a"}), 1: frozenset()},
        )
        nba = NBA(
            states=[(0, 1), (1, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset({(1, 1)}),
            transitions={
                (0, 1): {frozenset({"a"}): [(1, 1)]},
                (1, 1): {frozenset(): [(1, 1)]},
            },
            atomic_props=frozenset({"a"}),
        )
        product = product_ts_nba(ts, nba)
        assert len(product.initial_states) > 0
        for s0, q0 in product.initial_states:
            assert s0 == 0
            assert q0 == (1, 1)

    def test_no_initial_states_when_nba_rejects_label(self):
        """No initial states when NBA has no transition on TS initial label."""
        ts = MockTS(
            initial_states=[0],
            successors_map={},
            label_map={0: frozenset({"b"})},
        )
        nba = NBA(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={(0, 1): {frozenset({"a"}): [(0, 1)]}},
            atomic_props=frozenset({"a"}),
        )
        product = product_ts_nba(ts, nba)
        assert product.initial_states == []

    def test_multiple_initial_ts_states(self):
        """Each TS initial state paired with NBA successor."""
        ts = MockTS(
            initial_states=[0, 1],
            successors_map={},
            label_map={0: frozenset({"a"}), 1: frozenset({"b"})},
        )
        nba = NBA(
            states=[(0, 1), (1, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={
                (0, 1): {frozenset({"a"}): [(1, 1)], frozenset({"b"}): [(0, 1)]}
            },
            atomic_props=frozenset({"a", "b"}),
        )
        product = product_ts_nba(ts, nba)
        ts_indices = {s for s, _ in product.initial_states}
        assert 0 in ts_indices
        assert 1 in ts_indices


class TestProductTransitions:
    """Test product automaton transitions."""

    def test_transition_reads_destination_label(self):
        """NBA reads L(t) not L(s) when building (s,q)->(t,p)."""
        ts = MockTS(
            initial_states=[0],
            successors_map={0: [1]},
            label_map={0: frozenset({"a"}), 1: frozenset({"b"})},
        )
        nba = NBA(
            states=[(0, 1), (1, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={
                (0, 1): {frozenset({"a"}): [(1, 1)]},
                (1, 1): {frozenset({"b"}): [(0, 1)]},
            },
            atomic_props=frozenset({"a", "b"}),
        )
        product = product_ts_nba(ts, nba)
        init = product.initial_states[0]
        succs = product.transitions[init]
        assert (1, (0, 1)) in succs

    def test_no_transition_when_nba_blocks(self):
        """No product transition when NBA has no successor on L(t)."""
        ts = MockTS(
            initial_states=[0],
            successors_map={0: [1], 1: []},
            label_map={0: frozenset({"a"}), 1: frozenset({"c"})},
        )
        nba = NBA(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={(0, 1): {frozenset({"a"}): [(0, 1)]}},
            atomic_props=frozenset({"a", "b"}),
        )
        product = product_ts_nba(ts, nba)
        assert len(product.initial_states) > 0
        ts_states = {s for s, _ in product.states}
        assert 1 not in ts_states


class TestProductReachability:
    """Test product automaton reachability."""

    def test_only_reachable_states_included(self):
        """Unreachable TS states do not appear in product."""
        ts = MockTS(
            initial_states=[0],
            successors_map={0: [1], 1: []},
            label_map={0: frozenset(), 1: frozenset()},
        )
        nba = NBA(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={(0, 1): {frozenset(): [(0, 1)]}},
            atomic_props=frozenset(),
        )
        product = product_ts_nba(ts, nba)
        ts_states = {s for s, _ in product.states}
        assert 0 in ts_states
        assert 1 in ts_states
        assert 2 not in ts_states

    def test_all_reachable_states_have_transitions(self):
        """Every reachable product state has an entry in transitions."""
        ts = MockTS(
            initial_states=[0],
            successors_map={0: [1], 1: []},
            label_map={0: frozenset(), 1: frozenset()},
        )
        nba = NBA(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={(0, 1): {frozenset(): [(0, 1)]}},
            atomic_props=frozenset(),
        )
        product = product_ts_nba(ts, nba)
        for state in product.states:
            assert state in product.transitions


class TestProductAccepting:
    """Test product automaton accepting states."""

    def test_accepting_states_match_nba_acceptance_set(self):
        """(s,q) is accepting iff q in nba.acceptance_set."""
        ts = MockTS(
            initial_states=[0], successors_map={0: []}, label_map={0: frozenset()}
        )
        nba = NBA(
            states=[(0, 1), (1, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset({(1, 1)}),
            transitions={(0, 1): {frozenset(): [(1, 1)]}},
            atomic_props=frozenset(),
        )
        product = product_ts_nba(ts, nba)
        for s, q in product.states:
            is_accepting = (s, q) in product.accepting_states
            nba_accepting = q in nba.acceptance_set
            assert is_accepting == nba_accepting

    def test_non_accepting_nba_state_not_in_accepting(self):
        """(s,q0) not in accepting_states when q0 not in acceptance_set."""
        ts = MockTS(initial_states=[0], successors_map={}, label_map={0: frozenset()})
        nba = NBA(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            acceptance_set=frozenset(),
            transitions={(0, 1): {frozenset(): [(0, 1)]}},
            atomic_props=frozenset(),
        )
        product = product_ts_nba(ts, nba)
        for s, q in product.states:
            if q not in nba.acceptance_set:
                assert (s, q) not in product.accepting_states
