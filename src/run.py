import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.automata.gnba import ltl_to_gnba
from src.automata.nba import gnba_to_nba
from src.automata.ndfs import check_persistence
from src.automata.product import product_ts_nba
from src.cli.benchmark import parse_benchmark
from src.parser.ast_nodes import Not
from src.parser.parser import parse
from src.ts.transition_system import TransitionSystem


def main():
    parser = argparse.ArgumentParser(description="LTL model checker")
    parser.add_argument("folder", help="Path to benchmark folder")
    parser.add_argument("--verbose", action="store_true", help="Print pipeline details")
    args = parser.parse_args()

    folder = Path(args.folder)

    # Load TS from folder/TS.txt
    ts_path = folder / "TS.txt"
    ts = TransitionSystem.load(ts_path, args.verbose)

    # Parse benchmark from folder/benchmark.txt
    benchmark_path = folder / "benchmark.txt"
    global_formulas, local_formulas = parse_benchmark(
        benchmark_path, verbose=args.verbose
    )

    def run(check_ts, formula_str, verbose=False):
        formula = parse(formula_str)
        gnba = ltl_to_gnba(Not(formula), verbose=verbose)
        nba = gnba_to_nba(gnba, verbose=verbose)
        product = product_ts_nba(check_ts, nba, verbose=verbose)
        return check_persistence(product).satisfied

    for formula_str in global_formulas:
        print(1 if run(ts, formula_str, verbose=args.verbose) else 0)

    for state_index, formula_str in local_formulas:
        local_ts = TransitionSystem(
            num_states=ts.num_states,
            initial_states=frozenset({state_index}),
            actions=ts.actions,
            atomic_props=ts.atomic_props,
            transitions=ts.transitions,
            labels=ts.labels,
        )
        print(1 if run(local_ts, formula_str, verbose=args.verbose) else 0)


if __name__ == "__main__":
    main()
