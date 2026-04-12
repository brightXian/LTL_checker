# Implementation Document

## Table of Contents

1. [Code Structure](#1-code-structure)
2. [Data Structures](#2-data-structures)
3. [Step 1 — LTL Parser](#3-step-1--ltl-parser)
4. [Step 2–3 — LTL to GNBA](#4-step-23--ltl-to-gnba)
5. [Step 4a — GNBA to NBA](#5-step-4a--gnba-to-nba)
6. [Step 4b — Product TS](#6-step-4b--product-ts)
7. [Step 5 — Nested DFS](#7-step-5--nested-dfs)
8. [Main Pipeline](#8-main-pipeline)

---

## 1. Code Structure

```
src/
├── run.py                    # Main entry point
├── parser/
│   ├── ast_nodes.py          # 9 AST node types (dataclasses)
│   ├── lexer.py              # Regex-based tokenizer
│   └── parser.py             # Recursive descent parser
├── ts/
│   └── transition_system.py  # TransitionSystem dataclass + file loader
├── automata/
│   ├── closure.py            # Formula rewriting, closure, elementary sets
│   ├── gnba.py               # GNBA dataclass + ltl_to_gnba()
│   ├── nba.py                # NBA dataclass + gnba_to_nba()
│   ├── product.py            # Product TS construction
│   └── ndfs.py               # Nested DFS
└── cli/
    └── benchmark.py          # Benchmark file parser
```

The `automata/` module is split by responsibility: `closure.py` handles all mathematical operations on LTL formulas (rewriting, closure computation, elementary set enumeration), while `gnba.py` focuses solely on GNBA construction using the results from `closure.py`. This mirrors the separation in the reference C++ implementation (`ClosureAnalyzer` vs `fromLTL`).

---

## 2. Data Structures

### TransitionSystem

```python
@dataclass
class TransitionSystem:
    num_states: int
    initial_states: frozenset[int]           # indices of initial states
    actions: list[str]                        # action names
    atomic_props: list[str]                   # AP names
    transitions: list[tuple[int, int, int]]   # (from_state, action_idx, to_state)
    labels: list[frozenset[str]]              # labels[i] = L(s_i) ⊆ AP
```

### GNBA

```python
@dataclass
class GNBA:
    states: list[frozenset[str]]
    initial_states: list[frozenset[str]]
    acceptance_sets: list[frozenset[frozenset[str]]]   # one set per Until subformula
    transitions: dict[int, dict[frozenset[str], list[int]]]
    atomic_props: frozenset[str]
```

Each GNBA state is a `frozenset[str]`, where each string is `str(node)` for some AST node. This allows formula membership tests using Python's `in` operator directly on the set.

The transition map `transitions[i][ap_set]` stores only one key per state: `B ∩ AP`. Queries for any other AP set return `[]` via `.get(A, [])`.

### NBA

```python
@dataclass
class NBA:
    states: list[tuple[int, int]]
    initial_states: list[tuple[int, int]]
    acceptance_set: frozenset[tuple[int, int]]
    transitions: dict[tuple[int, int], dict[frozenset[str], list[tuple[int, int]]]]
    atomic_props: frozenset[str]
```

NBA states are tuples `(q, i)` where `q` is the GNBA state index and `i ∈ {1, ..., k}` is the layer number (1-indexed).

---

## 3. Step 1 — LTL Parser

**Module:** `src/parser/`

**Lexer (`lexer.py`):** A regex-based tokenizer recognizing atoms (identifiers), operators (`!`, `/\`, `\/`, `->`, `X`, `G`, `F`, `U`), and parentheses.

**Parser (`parser.py`):** A recursive descent parser with two mutually recursive functions:

- `parse_primary()` — handles atoms, parenthesized expressions, and unary operators (`!`, `X`, `G`, `F`). Unary operators recurse into `parse_primary()` for their child, not `parse_formula()`. This prevents greedy consumption of subsequent binary operators.
- `parse_formula()` — handles binary operators (`/\`, `\/`, `->`, `U`) by calling `parse_primary()` for the left operand, then checking for a binary operator.

**AST nodes (`ast_nodes.py`):** Nine dataclasses — `Atom`, `Not`, `And`, `Or`, `Imply`, `Next`, `Globally`, `Finally`, `Until`. Each implements `__str__` and `__eq__`.

---

## 4. Step 2–3 — LTL to GNBA

**Module:** `src/automata/closure.py` + `src/automata/gnba.py`

This step implements **Theorem 5.37** (Baier & Katoen, p. 278).

### 4.1 Formula Rewriting (`closure.py: _rewrite`)

Before closure computation, the formula is rewritten to use only the basic operators `{Atom, Not, And, Next, Until}`:

| Original | Rewritten |
|----------|-----------|
| `Or(a, b)` | `Not(And(Not(a), Not(b)))` |
| `Imply(a, b)` | `Not(And(a, Not(b)))` |
| `Finally(a)` | `Until(TRUE_ATOM, a)` |
| `Globally(a)` | `Not(Until(TRUE_ATOM, Not(a)))` |
| `Not(Not(x))` | `x` |

`TRUE_ATOM = Atom("__true__")` is a sentinel proposition that always holds. It is introduced as the left operand of `Until` when expanding `F` and `G`.

Double negation is eliminated eagerly via `_negate()`: instead of constructing `Not(Not(x))`, `_negate(Not(x))` returns `x` directly. This avoids spurious duplicates in the closure.

### 4.2 Closure Computation (`closure.py: _compute_closure`)

The closure of a rewritten formula `φ` is:

```
Closure(φ) = { ψ | ψ is a subformula of φ } ∪ { ¬ψ | ψ is a subformula of φ }
```

The result is a deduplicated list of `ASTNode` objects, using `str(node)` as the deduplication key.

### 4.3 Elementary Set Enumeration (`closure.py: _is_elementary`, `_compute_elementary_sets`)

An **elementary set** `B ⊆ Closure(φ)` (represented as `frozenset[str]`) satisfies four conditions (Figure 5.20, p. 277):

1. **And-consistency:** `And(a,b) ∈ B ↔ a ∈ B ∧ b ∈ B`
2. **Negation-consistency + Maximality:** for every `ψ ∈ Closure(φ)`, exactly one of `{ψ, ¬ψ}` is in `B`. Both conditions are checked in a **single loop** since they both examine the same pair:
   ```python
   for psi in closure:
       psi_str = str(psi)
       neg_str = str(_negate(psi))
       if psi_str in b and neg_str in b: return False      # negation-consistency
       if psi_str not in b and neg_str not in b: return False  # maximality
   ```
3. **TRUE_ATOM:** if `TRUE_ATOM ∈ Closure(φ)` then `TRUE_ATOM ∈ B`
4. **Until-consistency:**
   - `b ∈ B ⟹ (a U b) ∈ B`
   - `(a U b) ∈ B ∧ b ∉ B ⟹ a ∈ B`

All elementary sets are found by iterating over all `2^|Closure(φ)|` subsets and testing each one.

### 4.4 GNBA Construction (`gnba.py: ltl_to_gnba`)

| Component | Definition |
|-----------|------------|
| States | all elementary sets |
| Initial states | `{ B \| str(φ) ∈ B }` |
| Acceptance sets | one per `Until(a,b)` in closure: `{ B \| (aUb) ∉ B ∨ b ∈ B }` |

**Transitions (`_build_transitions`):** `B →_A B'` iff:
- `A = B ∩ AP`
- **Next-consistency:** `X(ψ) ∈ B ↔ ψ ∈ B'`
- **Until-consistency:**
  - If `(a U b) ∈ B`: `b ∈ B`, or (`a ∈ B` and `(a U b) ∈ B'`)
  - If `(a U b) ∉ B`: not (`a ∈ B` and `(a U b) ∈ B'`)

### Example: `φ = a U b`

Closure: `{ (a U b), !((a U b)), a, !(a), b, !(b) }`

Elementary sets:

| State | Contents |
|-------|----------|
| B₁ | `{(a U b), a, b}` |
| B₂ | `{(a U b), !(a), b}` |
| B₃ | `{(a U b), a, !(b)}` |
| B₄ | `{!((a U b)), !(a), !(b)}` |
| B₅ | `{!((a U b)), a, !(b)}` |

Initial states Q₀ = {B₁, B₂, B₃}. Acceptance set F = {B₁, B₂, B₄, B₅}.

---

## 5. Step 4a — GNBA to NBA

**Module:** `src/automata/nba.py`

Implements **Theorem 4.56** (p. 195).

**Special case `k = 0`:** no acceptance constraints — all states are accepting. A single-layer NBA is built with all states in the acceptance set.

**General case `k ≥ 1`:** create `k` copies of the GNBA state space.

| Component | Definition |
|-----------|------------|
| States | `(q, i)` for all `q`, `i ∈ {1,...,k}` |
| Initial states | `(q, 1)` for each `q` in GNBA initial states |
| Acceptance set | `{ (q, 1) \| states[q] ∈ F₁ }` |
| Transition from `(q, i)` | if `states[q] ∉ Fᵢ`: successors go to layer `i`; if `states[q] ∈ Fᵢ`: successors go to layer `(i mod k) + 1` |

The automaton advances to the next layer only upon visiting an accepting state of the current layer. A run visits layer 1 infinitely often if and only if it visits all `Fᵢ` infinitely often.

---

## 6. Step 4b — Product TS

**Module:** `src/automata/product.py`

Implements **Definition 4.62** (p. 200).

### Transition Rule

```
s -α→ t  ∧  q --L(t)→ p
─────────────────────────
    ⟨s, q⟩ -α→ ⟨t, p⟩
```

The NBA reads `L(t)` — the label of the **destination** state `t`, not the current state `s`.

### Initial States

```
I' = { ⟨s₀, q⟩ | s₀ ∈ I, ∃q₀ ∈ Q₀. q₀ --L(s₀)→ q }
```

This is **not** simply `I × Q₀`. For each initial TS state `s₀` and each NBA initial state `q₀`, one step is taken reading `L(s₀)`; only the resulting states `q` are used. If no `q₀` has a transition on `L(s₀)`, then `I' = ∅` and the product TS is empty — meaning the negated formula's language has no intersection with the TS traces, so `TS ⊨ φ` and the result is `1`.

### Local vs. Global Formulas

For **global formulas**, `run.py` passes the original TS with its full set of initial states to the product construction.

For **local formulas on state `sᵢ`**, `run.py` creates a modified `TransitionSystem` with `initial_states = frozenset({i})` before passing it to the product construction. The product thus starts only from `sᵢ`.

### Acceptance Set

```
F' = { ⟨s, q⟩ | q ∈ F_NBA }
```

---

## 7. Step 5 — Nested DFS

**Module:** `src/automata/ndfs.py`

Implements **Algorithm 8** (p. 211). Determines whether the product TS contains a reachable accepting cycle.

### Algorithm

Two visited sets are maintained:

- `r`: states visited by the **outer DFS**
- `t`: states visited by the **inner DFS**, **shared across all inner DFS calls**

```
function nested_dfs(product_ts):
    r ← ∅,  t ← ∅
    for each initial state s₀:
        if s₀ ∉ r: outer_dfs(s₀)
    return False

function outer_dfs(s):
    r.add(s)
    for each successor s' of s:
        if s' ∉ r: outer_dfs(s')
    if s ∈ F:                         # s is an accepting state
        if inner_dfs(s, s): raise CycleFound

function inner_dfs(seed, s):
    t.add(s)
    for each successor s' of s:
        if s' == seed: raise CycleFound   # back edge to seed
        if s' ∉ t: inner_dfs(seed, s')
```

### Key Design Decisions

**Post-order outer DFS:** the outer DFS launches the inner DFS only after fully exploring all descendants of an accepting state. This ensures that when `inner_dfs(s)` is called, any cycle through `s` that goes through states deeper in the DFS tree has already been checked.

**Shared inner visited set `t`:** `t` is not reset between inner DFS calls. Once a state is explored in any inner DFS, it need not be explored again: if a cycle existed through that state, it would have been detected in the call that first visited it. Sharing `t` is therefore both correct and more efficient.

**Cycle detection:** the inner DFS checks if any successor of the current state equals the seed (the accepting state that started this inner DFS). A match means there is a cycle from the seed back to itself, which is an accepting cycle.

### Correctness

The algorithm is correct because:
- The outer DFS visits all accepting states reachable from the initial states.
- For each such accepting state `s`, the inner DFS checks whether a path from `s` leads back to `s`.
- The shared `t` set preserves correctness: if a state `u` has been fully explored in a previous inner DFS without finding a cycle, no subsequent inner DFS starting from a different seed can find a new cycle through `u` that was not already detectable from that earlier call.

### Result Interpretation

- **Accepting cycle found:** the negated formula `¬φ` has a witness trace in the TS → `TS ⊭ φ` → output `0`.
- **No accepting cycle:** `Traces(TS) ∩ Lω(A) = ∅` → `TS ⊨ φ` → output `1`.

---

## 8. Main Pipeline

**Module:** `src/run.py`

For each formula in the benchmark:

1. Parse the LTL formula into an AST (`src/parser/`).
2. Negate it: `Not(formula)`.
3. Construct the GNBA for `¬φ`: `ltl_to_gnba(Not(formula))`.
4. Convert to NBA: `gnba_to_nba(gnba)`.
5. Build the product TS: for global formulas, use the original TS; for local formulas, create a copy with `initial_states = frozenset({state_index})`.
6. Run nested DFS: `nested_dfs(product_ts)`.
7. Output `0` if an accepting cycle is found, `1` otherwise.
