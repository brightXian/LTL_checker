"""Tests for TransitionSystem."""

import textwrap

import pytest

from src.ts.transition_system import TransitionSystem

TS_CONTENT = textwrap.dedent("""\
    6 9
    0
    0 1 2
    a b c
    0 1 1
    0 0 3
    3 2 1
    1 2 4
    2 2 1
    5 0 2
    5 1 1
    4 0 1
    4 1 5
    0 1
    0 1 2
    1 2
    0 2
    0 2
    0 1
""")


@pytest.fixture
def ts_file(tmp_path):
    """Create a temporary TS.txt file."""
    ts_path = tmp_path / "TS.txt"
    ts_path.write_text(TS_CONTENT)
    return ts_path


@pytest.fixture
def ts(ts_file):
    """Load the transition system from the temporary file."""
    return TransitionSystem.load(ts_file)


class TestBasicLoading:
    """Tests for basic loading."""

    def test_num_states(self, ts):
        """The number of states equals 6."""
        assert ts.num_states == 6

    def test_initial_states(self, ts):
        """The initial state is state 0."""
        assert ts.initial_states == frozenset({0})

    def test_atomic_props(self, ts):
        """The atomic propositions are a, b, c."""
        assert ts.atomic_props == ["a", "b", "c"]

    def test_num_transitions(self, ts):
        """The number of transitions equals 9."""
        assert len(ts.transitions) == 9


class TestLabels:
    """Tests for state labels."""

    def test_label_0(self, ts):
        """State 0 is labeled with a and b."""
        assert ts.labels[0] == frozenset({"a", "b"})

    def test_label_1(self, ts):
        """State 1 is labeled with a, b, and c."""
        assert ts.labels[1] == frozenset({"a", "b", "c"})

    def test_label_2(self, ts):
        """State 2 is labeled with b and c."""
        assert ts.labels[2] == frozenset({"b", "c"})

    def test_label_3(self, ts):
        """State 3 is labeled with a and c."""
        assert ts.labels[3] == frozenset({"a", "c"})

    def test_label_4(self, ts):
        """State 4 is labeled with a and c."""
        assert ts.labels[4] == frozenset({"a", "c"})

    def test_label_5(self, ts):
        """State 5 is labeled with a and b."""
        assert ts.labels[5] == frozenset({"a", "b"})


class TestPost:
    """Tests for post() method."""

    def test_post_0(self, ts):
        """State 0 has successors 1 and 3."""
        assert ts.post(0) == frozenset({1, 3})

    def test_post_1(self, ts):
        """State 1 has successor 4."""
        assert ts.post(1) == frozenset({4})

    def test_post_2(self, ts):
        """State 2 has successor 1."""
        assert ts.post(2) == frozenset({1})

    def test_post_3(self, ts):
        """State 3 has successor 1."""
        assert ts.post(3) == frozenset({1})

    def test_post_4(self, ts):
        """State 4 has successors 1 and 5."""
        assert ts.post(4) == frozenset({1, 5})

    def test_post_5(self, ts):
        """State 5 has successors 1 and 2."""
        assert ts.post(5) == frozenset({1, 2})


class TestEmptyLabel:
    """Tests for empty label state."""

    def test_empty_label(self, tmp_path):
        """A state with label -1 has an empty label set."""
        content = textwrap.dedent("""\
            2 1
            0
            a b
            a b
            0 1 1
            -1
            0 1
        """)
        ts_path = tmp_path / "TS.txt"
        ts_path.write_text(content)
        ts = TransitionSystem.load(ts_path)
        assert ts.labels[0] == frozenset()
        assert ts.labels[1] == frozenset({"a", "b"})


class TestMultipleInitialStates:
    """Tests for multiple initial states."""

    def test_multiple_initial(self, tmp_path):
        """Multiple initial states are parsed correctly."""
        content = textwrap.dedent("""\
            2 1
            0 1
            a b
            a b
            0 0 1
            0
            0
        """)
        ts_path = tmp_path / "TS.txt"
        ts_path.write_text(content)
        ts = TransitionSystem.load(ts_path)
        assert ts.initial_states == frozenset({0, 1})


class TestErrors:
    """Tests for error cases."""

    def test_fewer_than_four_lines(self, tmp_path):
        """A file with fewer than 4 lines raises ValueError."""
        content = textwrap.dedent("""\
            1 1
            0
            a
        """)
        ts_path = tmp_path / "TS.txt"
        ts_path.write_text(content)
        with pytest.raises(ValueError):
            TransitionSystem.load(ts_path)

    def test_invalid_state_in_transition(self, tmp_path):
        """An out-of-range state index in a transition raises ValueError."""
        content = textwrap.dedent("""\
            2 1
            0
            a b
            a b
            10 0 1
            0
            0
        """)
        ts_path = tmp_path / "TS.txt"
        ts_path.write_text(content)
        with pytest.raises(ValueError):
            TransitionSystem.load(ts_path)

    def test_invalid_ap_index(self, tmp_path):
        """An invalid AP index in a label raises ValueError."""
        content = textwrap.dedent("""\
            2 1
            0
            a b
            a b
            0 0 1
            5
            0
        """)
        ts_path = tmp_path / "TS.txt"
        ts_path.write_text(content)
        with pytest.raises(ValueError):
            TransitionSystem.load(ts_path)

    def test_invalid_initial_state(self, tmp_path):
        """An out-of-range initial state index raises ValueError."""
        content = textwrap.dedent("""\
            2 1
            99
            a b
            a b
            0 0 1
            0
            0
        """)
        ts_path = tmp_path / "TS.txt"
        ts_path.write_text(content)
        with pytest.raises(ValueError):
            TransitionSystem.load(ts_path)

    def test_post_out_of_range(self, ts):
        """An out-of-range state index in post() raises ValueError."""
        with pytest.raises(ValueError):
            ts.post(100)
