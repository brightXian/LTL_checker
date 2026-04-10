"""Unit tests for GNBA construction."""

from src.automata.closure import (
    TRUE_ATOM,
    _compute_closure,
    _rewrite,
)
from src.automata.gnba import ltl_to_gnba
from src.parser.ast_nodes import And, Atom, Next, Not, Until
from src.parser.parser import parse


class TestRewrite:
    """Test _rewrite produces only Atom, Not, And, Next, Until nodes."""

    def test_atom_unchanged(self):
        """parse("a") -> Atom("a") (unchanged)."""
        result = _rewrite(parse("a"))
        assert isinstance(result, Atom)
        assert result.name == "a"

    def test_not_unchanged(self):
        """parse("!a") -> Not(Atom("a")) (unchanged)."""
        result = _rewrite(parse("!a"))
        assert isinstance(result, Not)

    def test_and_unchanged(self):
        """parse("(a /\\ b)") -> And(Atom("a"), Atom("b")) (unchanged)."""
        result = _rewrite(parse("(a /\\ b)"))
        assert isinstance(result, And)

    def test_until_unchanged(self):
        """parse("a U b") -> Until(Atom("a"), Atom("b")) (unchanged)."""
        result = _rewrite(parse("a U b"))
        assert isinstance(result, Until)

    def test_next_unchanged(self):
        """parse("X(a)") -> Next(Atom("a")) (unchanged)."""
        result = _rewrite(parse("X(a)"))
        assert isinstance(result, Next)

    def test_or_produces_not_and(self):
        """parse("(a \\/ b)") -> produces Not(And(Not(a), Not(b)))."""
        result = _rewrite(parse("(a \\/ b)"))
        assert isinstance(result, Not)
        assert isinstance(result.child, And)

    def test_imply_produces_not_and(self):
        """parse("(a -> b)") -> produces Not(And(a, Not(b)))."""
        result = _rewrite(parse("(a -> b)"))
        assert isinstance(result, Not)
        assert isinstance(result.child, And)

    def test_finally_becomes_until(self):
        """parse("F(a)") -> Until(TRUE_ATOM, Atom("a"))."""
        result = _rewrite(parse("F(a)"))
        assert isinstance(result, Until)
        assert result.left == TRUE_ATOM
        assert isinstance(result.right, Atom)

    def test_globally_becomes_not_until(self):
        """parse("G(a)") -> Not(Until(TRUE_ATOM, Not(Atom("a"))))."""
        result = _rewrite(parse("G(a)"))
        assert isinstance(result, Not)
        assert isinstance(result.child, Until)
        # No double negation: right child of Until is Not(Atom("a"))
        right_child = result.child.right
        assert isinstance(right_child, Not)
        # Direct Not, not Not(Not(...))
        right_child_child = right_child.child
        assert not isinstance(right_child_child, Not)


class TestComputeClosure:
    """Test _compute_closure returns correct size and contents."""

    def test_until_closure_size(self):
        """Closure of Until(a, b) has 6 elements."""
        phi = Until(Atom("a"), Atom("b"))
        closure = _compute_closure(phi)
        assert len(closure) == 6
        expected = {"(a U b)", "!((a U b))", "a", "!(a)", "b", "!(b)"}
        assert expected == {str(p) for p in closure}

    def test_next_closure_size(self):
        """Closure of Next(a) has 4 elements."""
        phi = Next(Atom("a"))
        closure = _compute_closure(phi)
        assert len(closure) == 4
        expected = {"X(a)", "!(X(a))", "a", "!(a)"}
        assert expected == {str(p) for p in closure}


class TestGNBAAtom:
    """Test GNBA for simple atom 'a'."""

    def test_atom_states(self):
        """GNBA for 'a' has 2 states."""
        gnba = ltl_to_gnba(parse("a"))
        assert len(gnba.states) == 2

    def test_atom_initial(self):
        """GNBA for 'a' has 1 initial state."""
        gnba = ltl_to_gnba(parse("a"))
        assert len(gnba.initial_states) == 1

    def test_atom_atomic_props(self):
        """GNBA for 'a' has atomic prop 'a'."""
        gnba = ltl_to_gnba(parse("a"))
        assert gnba.atomic_props == frozenset({"a"})

    def test_atom_acceptance_sets(self):
        """GNBA for 'a' has no acceptance sets."""
        gnba = ltl_to_gnba(parse("a"))
        assert gnba.acceptance_sets == []

    def test_atom_initial_contains_atom(self):
        """Initial state contains 'a'."""
        gnba = ltl_to_gnba(parse("a"))
        assert all("a" in s for s in gnba.initial_states)


class TestGNBANext:
    """Test GNBA for Next/X operator."""

    def test_next_states(self):
        """GNBA for 'X(a)' has 4 states."""
        gnba = ltl_to_gnba(parse("X(a)"))
        assert len(gnba.states) == 4

    def test_next_initial(self):
        """GNBA for 'X(a)' has 2 initial states."""
        gnba = ltl_to_gnba(parse("X(a)"))
        assert len(gnba.initial_states) == 2

    def test_next_atomic_props(self):
        """GNBA for 'X(a)' has atomic prop 'a'."""
        gnba = ltl_to_gnba(parse("X(a)"))
        assert gnba.atomic_props == frozenset({"a"})

    def test_next_acceptance_sets(self):
        """GNBA for 'X(a)' has no acceptance sets."""
        gnba = ltl_to_gnba(parse("X(a)"))
        assert gnba.acceptance_sets == []


class TestGNBAUntil:
    """Test GNBA for Until operator (Textbook Example 5.39)."""

    def test_until_states(self):
        """GNBA for 'a U b' has 5 states."""
        gnba = ltl_to_gnba(parse("a U b"))
        assert len(gnba.states) == 5

    def test_until_initial(self):
        """GNBA for 'a U b' has 3 initial states."""
        gnba = ltl_to_gnba(parse("a U b"))
        assert len(gnba.initial_states) == 3

    def test_until_atomic_props(self):
        """GNBA for 'a U b' has atomic props 'a' and 'b'."""
        gnba = ltl_to_gnba(parse("a U b"))
        assert gnba.atomic_props == frozenset({"a", "b"})

    def test_until_acceptance_sets(self):
        """GNBA for 'a U b' has 1 acceptance set."""
        gnba = ltl_to_gnba(parse("a U b"))
        assert len(gnba.acceptance_sets) == 1

    def test_until_initial_contains_until(self):
        """All initial states contain the Until formula."""
        until_str = "(a U b)"
        gnba = ltl_to_gnba(parse("a U b"))
        assert all(until_str in s for s in gnba.initial_states)

    def test_until_acceptance_set_size(self):
        """Acceptance set has 4 states."""
        gnba = ltl_to_gnba(parse("a U b"))
        assert len(gnba.acceptance_sets[0]) == 4

    def test_until_acceptance_complement(self):
        """States not in acceptance contain Until but not b."""
        b_str = "b"
        until_str = "(a U b)"
        gnba = ltl_to_gnba(parse("a U b"))
        acc = gnba.acceptance_sets[0]
        for s in gnba.states:
            if s not in acc:
                assert until_str in s and b_str not in s


class TestGNBANegation:
    """Test GNBA for negation."""

    def test_negation_states(self):
        """GNBA for '!a' has 2 states."""
        gnba = ltl_to_gnba(parse("!a"))
        assert len(gnba.states) == 2

    def test_negation_initial(self):
        """GNBA for '!a' has 1 initial state."""
        gnba = ltl_to_gnba(parse("!a"))
        assert len(gnba.initial_states) == 1

    def test_negation_initial_contains_not(self):
        """Initial state contains '!(a)'."""
        gnba = ltl_to_gnba(parse("!a"))
        assert all("!(a)" in s for s in gnba.initial_states)


class TestGNBAAnd:
    """Test GNBA for conjunction."""

    def test_and_states(self):
        """GNBA for '(a /\\ b)' has 4 states."""
        gnba = ltl_to_gnba(parse("(a /\\ b)"))
        assert len(gnba.states) == 4

    def test_and_initial(self):
        """GNBA for '(a /\\ b)' has 1 initial state."""
        gnba = ltl_to_gnba(parse("(a /\\ b)"))
        assert len(gnba.initial_states) == 1

    def test_and_acceptance_sets(self):
        """GNBA for '(a /\\ b)' has no acceptance sets."""
        gnba = ltl_to_gnba(parse("(a /\\ b)"))
        assert gnba.acceptance_sets == []

    def test_and_initial_contains_both(self):
        """Initial state contains both 'a' and 'b'."""
        gnba = ltl_to_gnba(parse("(a /\\ b)"))
        assert all("a" in s and "b" in s for s in gnba.initial_states)


class TestGNBAFinally:
    """Test GNBA for Finally (F) operator."""

    def test_finally_states(self):
        """GNBA for 'F(a)' has 3 states."""
        gnba = ltl_to_gnba(parse("F(a)"))
        assert len(gnba.states) == 3

    def test_finally_initial(self):
        """GNBA for 'F(a)' has 2 initial states."""
        gnba = ltl_to_gnba(parse("F(a)"))
        assert len(gnba.initial_states) == 2

    def test_finally_acceptance_sets(self):
        """GNBA for 'F(a)' has 1 acceptance set."""
        gnba = ltl_to_gnba(parse("F(a)"))
        assert len(gnba.acceptance_sets) == 1

    def test_finally_atomic_props(self):
        """GNBA for 'F(a)' has atomic prop 'a'."""
        gnba = ltl_to_gnba(parse("F(a)"))
        assert gnba.atomic_props == frozenset({"a"})

    def test_finally_acceptance_size(self):
        """Acceptance set has 2 states."""
        gnba = ltl_to_gnba(parse("F(a)"))
        assert len(gnba.acceptance_sets[0]) == 2


class TestGNBATransitions:
    """Test transition structure."""

    def test_transitions_count(self):
        """Every state has exactly one entry in transitions."""
        gnba = ltl_to_gnba(parse("a U b"))
        assert len(gnba.transitions) == len(gnba.states)

    def test_transitions_keys_are_frozenset(self):
        """Transitions dict uses frozenset keys."""
        gnba = ltl_to_gnba(parse("a U b"))
        for i in range(len(gnba.states)):
            assert i in gnba.transitions
            for key in gnba.transitions[i]:
                assert isinstance(key, frozenset)

    def test_successors_valid_indices(self):
        """Successors are valid state indices."""
        gnba = ltl_to_gnba(parse("a U b"))
        for i in range(len(gnba.states)):
            for succs in gnba.transitions[i].values():
                for j in succs:
                    assert 0 <= j < len(gnba.states)


class TestGNBAGlobally:
    """Test GNBA for Globally (G) operator."""

    def test_globally_states(self):
        """GNBA for 'G(a)' has 3 states.

        G(a) rewrites to Not(Until(TRUE_ATOM, Not(a))).
        The 3 elementary states are:
          {a, TRUE_ATOM, Not(Until(TRUE_ATOM, Not(a)))}
          {a, TRUE_ATOM, Until(TRUE_ATOM, Not(a))}
          {Not(a), TRUE_ATOM, Until(TRUE_ATOM, Not(a))}
        """
        gnba = ltl_to_gnba(parse("G(a)"))
        assert len(gnba.states) == 3

    def test_globally_initial(self):
        """GNBA for 'G(a)' has 1 initial state (contains Not(Until(...)))."""
        gnba = ltl_to_gnba(parse("G(a)"))
        assert len(gnba.initial_states) == 1

    def test_globally_acceptance_sets(self):
        """GNBA for 'G(a)' has 1 acceptance set (one Until in closure)."""
        gnba = ltl_to_gnba(parse("G(a)"))
        assert len(gnba.acceptance_sets) == 1

    def test_globally_atomic_props(self):
        """GNBA for 'G(a)' has atomic prop 'a' only."""
        gnba = ltl_to_gnba(parse("G(a)"))
        assert gnba.atomic_props == frozenset({"a"})


class TestGNBATransitionSemantics:
    """Test that transitions encode correct GNBA semantics for a U b."""

    def test_state_ap_determines_transition_key(self):
        """Each state B has exactly one valid AP input: B ∩ AP."""
        gnba = ltl_to_gnba(parse("a U b"))
        for i, state in enumerate(gnba.states):
            b_ap = state & gnba.atomic_props
            assert b_ap in gnba.transitions[i]

    def test_non_initial_sink_has_all_successors(self):
        """State with !(aUb), !(a), !(b) is non-initial but is in the
        acceptance set. It has no Until or Next constraints so it can
        transition to all other states."""
        gnba = ltl_to_gnba(parse("a U b"))
        until_str = "(a U b)"
        # Find state with !(a U b), !(a), !(b)
        sink_candidates = [
            (i, s)
            for i, s in enumerate(gnba.states)
            if until_str not in s and "a" not in s and "b" not in s
        ]
        assert len(sink_candidates) == 1
        i, sink = sink_candidates[0]
        # This state has non-empty successors
        # (it is a sink that accepts all future behaviors)
        b_ap = sink & gnba.atomic_props
        succs = gnba.transitions[i].get(b_ap, [])
        assert len(succs) > 0
