"""Transition system representation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TransitionSystem:
    """Represents a transition system for model checking."""

    num_states: int
    initial_states: frozenset[int]
    actions: list[str]
    atomic_props: list[str]
    # (from_state, action_index, to_state)
    transitions: list[tuple[int, int, int]]
    # labels[i] = set of AP names for state i
    labels: list[frozenset[str]]

    @classmethod
    def load(cls, filepath: str | Path) -> "TransitionSystem":
        """Load a transition system from a TS.txt file.

        Args:
            filepath: Path to the TS.txt file.

        Returns:
            TransitionSystem instance.

        Raises:
            ValueError: If the file format is malformed.
        """
        with open(filepath) as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) < 4:
            raise ValueError(
                f"File has fewer than 4 required lines, found {len(lines)}"
            )

        # Header: S T (number of states and transitions)
        try:
            parts = lines[0].split()
            if len(parts) != 2:
                raise ValueError(
                    f"Line 1 must have exactly 2 values (S T), found {len(parts)}"
                )
            num_states = int(parts[0])
            num_transitions = int(parts[1])
        except ValueError as e:
            raise ValueError(f"Error parsing line 1: {e}") from e

        # Initial states: space-separated indices
        try:
            initial_states = frozenset(int(x) for x in lines[1].split())
        except ValueError as e:
            raise ValueError(f"Error parsing initial states: {e}") from e

        # Validate initial state indices
        for s in initial_states:
            if s < 0 or s >= num_states:
                raise ValueError(f"Initial state {s} out of range [0, {num_states})")

        # Action identifiers: space-separated tokens from the file
        actions = lines[2].split()

        # Atomic proposition names: space-separated strings
        atomic_props = lines[3].split()

        # Expected total lines: 4 + num_transitions + num_states
        expected_lines = 4 + num_transitions + num_states
        if len(lines) < expected_lines:
            raise ValueError(
                f"Expected at least {expected_lines} lines (header + {num_transitions} transitions + {num_states} labels), "
                f"found {len(lines)}"
            )

        # Transitions: each line "i k j" means state i --action_k--> state j
        # Expected: T lines
        transitions: list[tuple[int, int, int]] = []
        for i in range(num_transitions):
            line = lines[4 + i]
            try:
                parts = line.split()
                if len(parts) != 3:
                    raise ValueError(
                        f"Transition line must have 3 values, found {len(parts)}"
                    )
                from_state = int(parts[0])
                action_index = int(parts[1])
                to_state = int(parts[2])
                if from_state < 0 or from_state >= num_states:
                    raise ValueError(
                        f"From state {from_state} out of range [0, {num_states})"
                    )
                if to_state < 0 or to_state >= num_states:
                    raise ValueError(
                        f"To state {to_state} out of range [0, {num_states})"
                    )
                if action_index < 0 or action_index >= len(actions):
                    raise ValueError(
                        f"Action index {action_index} out of range [0, {len(actions)})"
                    )
                transitions.append((from_state, action_index, to_state))
            except ValueError as e:
                if "out of range" in str(e):
                    raise
                raise ValueError(f"Error parsing transition line {i + 1}: {e}") from e

        # State labels: each line has space-separated AP indices, or "-1" for empty set
        # Expected: S lines
        labels_start = 4 + num_transitions
        labels: list[frozenset[str]] = []
        for i in range(num_states):
            line = lines[labels_start + i]
            if line == "-1":
                labels.append(frozenset())
            else:
                try:
                    ap_indices = [int(x) for x in line.split()]
                    ap_set = frozenset(atomic_props[idx] for idx in ap_indices)
                    labels.append(ap_set)
                except IndexError:
                    raise ValueError(
                        f"Invalid AP index in label for state {i}"
                    ) from None
                except ValueError as e:
                    raise ValueError(f"Error parsing label for state {i}: {e}") from e

        return cls(
            num_states=num_states,
            initial_states=initial_states,
            actions=actions,
            atomic_props=atomic_props,
            transitions=transitions,
            labels=labels,
        )

    def post(self, state: int) -> frozenset[int]:
        """Get all successor states reachable from the given state.

        Args:
            state: Source state index.

        Returns:
            Frozenset of successor state indices.

        Raises:
            ValueError: If state index is out of range.
        """
        if state < 0 or state >= self.num_states:
            raise ValueError(f"State index {state} out of range [0, {self.num_states})")

        successors: set[int] = set()
        for from_state, _action_index, to_state in self.transitions:
            if from_state == state:
                successors.add(to_state)

        return frozenset(successors)
