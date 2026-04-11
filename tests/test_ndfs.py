"""Unit tests for NDFS persistence check."""

from src.automata.ndfs import check_persistence
from src.automata.product import ProductTS


class TestNDFSSatisfied:
    """Test NDFS when persistence property holds."""

    def test_empty_product_satisfies(self):
        """Product with no states satisfies persistence."""
        product = ProductTS([], [], {}, frozenset())
        result = check_persistence(product)
        assert result.satisfied

    def test_no_accepting_states_satisfies(self):
        """Product with no accepting states always satisfies."""
        product = ProductTS(
            states=[(0, 0)],
            initial_states=[(0, 0)],
            transitions={(0, 0): [(0, 0)]},
            accepting_states=frozenset(),
        )
        result = check_persistence(product)
        assert result.satisfied

    def test_accepting_state_not_on_cycle_satisfies(self):
        """Accepting state is reachable but has no outgoing cycle."""
        product = ProductTS(
            states=[(0, 0), (1, 1)],
            initial_states=[(0, 0)],
            transitions={(0, 0): [(1, 1)], (1, 1): []},
            accepting_states=frozenset({(1, 1)}),
        )
        result = check_persistence(product)
        assert result.satisfied

    def test_non_accepting_cycle_satisfies(self):
        """Cycle exists but contains no accepting state."""
        product = ProductTS(
            states=[(0, 0), (1, 0)],
            initial_states=[(0, 0)],
            transitions={(0, 0): [(1, 0)], (1, 0): [(0, 0)]},
            accepting_states=frozenset(),
        )
        result = check_persistence(product)
        assert result.satisfied

    def test_unreachable_accepting_cycle_satisfies(self):
        """Accepting state on a cycle but unreachable from initial -> satisfied."""
        product = ProductTS(
            states=[(0, 0), (1, 1)],
            initial_states=[(0, 0)],
            transitions={
                (0, 0): [],
                (1, 1): [(1, 1)],
            },
            accepting_states=frozenset({(1, 1)}),
        )
        result = check_persistence(product)
        assert result.satisfied


class TestNDFSRefuted:
    """Test NDFS when persistence property is refuted."""

    def test_accepting_self_loop_refutes(self):
        """Accepting state with self-loop -> not satisfied."""
        product = ProductTS(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            transitions={(0, 1): [(0, 1)]},
            accepting_states=frozenset({(0, 1)}),
        )
        result = check_persistence(product)
        assert not result.satisfied

    def test_accepting_state_on_two_state_cycle_refutes(self):
        """Accepting state on a 2-state cycle -> not satisfied."""
        product = ProductTS(
            states=[(0, 1), (1, 0)],
            initial_states=[(0, 1)],
            transitions={(0, 1): [(1, 0)], (1, 0): [(0, 1)]},
            accepting_states=frozenset({(0, 1)}),
        )
        result = check_persistence(product)
        assert not result.satisfied

    def test_accepting_state_reachable_via_prefix_then_cycle_refutes(self):
        """Non-accepting prefix leads to accepting cycle -> not satisfied."""
        product = ProductTS(
            states=[(0, 0), (1, 1), (2, 1)],
            initial_states=[(0, 0)],
            transitions={
                (0, 0): [(1, 1)],
                (1, 1): [(2, 1)],
                (2, 1): [(1, 1)],
            },
            accepting_states=frozenset({(1, 1), (2, 1)}),
        )
        result = check_persistence(product)
        assert not result.satisfied


class TestNDFSCounterexample:
    """Test counterexample generation."""

    def test_counterexample_none_when_satisfied(self):
        """counterexample is None when property holds."""
        product = ProductTS(
            states=[(0, 0)],
            initial_states=[(0, 0)],
            transitions={(0, 0): []},
            accepting_states=frozenset(),
        )
        result = check_persistence(product)
        assert result.counterexample is None

    def test_counterexample_not_none_when_refuted(self):
        """counterexample is a non-empty list when refuted."""
        product = ProductTS(
            states=[(0, 1)],
            initial_states=[(0, 1)],
            transitions={(0, 1): [(0, 1)]},
            accepting_states=frozenset({(0, 1)}),
        )
        result = check_persistence(product)
        assert result.counterexample is not None
        assert len(result.counterexample) > 0

    def test_counterexample_contains_accepting_state(self):
        """At least one state in counterexample is an accepting state."""
        product = ProductTS(
            states=[(0, 1), (1, 0)],
            initial_states=[(0, 1)],
            transitions={(0, 1): [(1, 0)], (1, 0): [(0, 1)]},
            accepting_states=frozenset({(0, 1)}),
        )
        result = check_persistence(product)
        assert result.counterexample is not None
        assert any(s in product.accepting_states for s in result.counterexample)

    def test_counterexample_starts_from_initial_state(self):
        """Counterexample first state is an initial state."""
        product = ProductTS(
            states=[(0, 0), (1, 0), (2, 1)],
            initial_states=[(0, 0)],
            transitions={
                (0, 0): [(1, 0)],
                (1, 0): [(2, 1)],
                (2, 1): [(2, 1)],
            },
            accepting_states=frozenset({(2, 1)}),
        )
        result = check_persistence(product)
        assert result.counterexample is not None
        assert result.counterexample[0] in product.initial_states

    def test_counterexample_is_connected_path(self):
        """Each consecutive pair in counterexample is a valid transition."""
        product = ProductTS(
            states=[(0, 0), (1, 0), (2, 1)],
            initial_states=[(0, 0)],
            transitions={
                (0, 0): [(1, 0)],
                (1, 0): [(2, 1)],
                (2, 1): [(2, 1)],
            },
            accepting_states=frozenset({(2, 1)}),
        )
        result = check_persistence(product)
        path = result.counterexample
        assert path is not None
        for i in range(len(path) - 1):
            assert path[i + 1] in product.transitions.get(path[i], [])
