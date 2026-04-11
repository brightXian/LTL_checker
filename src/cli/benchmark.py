from pathlib import Path


def parse_benchmark(
    filepath: str | Path, verbose: bool = False
) -> tuple[list[str], list[tuple[int, str]]]:
    """Parse benchmark.txt into global and local LTL formulas."""
    with open(filepath) as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        raise ValueError("Benchmark file is empty")

    parts = lines[0].split()
    if len(parts) != 2:
        raise ValueError(
            f"First line must have exactly 2 values (A B), found {len(parts)}"
        )
    a, b = int(parts[0]), int(parts[1])

    global_formulas = [lines[1 + i] for i in range(a)]

    local_formulas = []
    for i in range(b):
        parts = lines[1 + a + i].split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(
                f"Local formula line must have 2 values, found {len(parts)}"
            )
        local_formulas.append((int(parts[0]), parts[1]))

    if verbose:
        print("[LTL Benchmark]")
        print("  Global formulas:")
        for _, f in enumerate(global_formulas):
            print(f"      {f}")
        print("  Local formulas:")
        for state_idx, f in local_formulas:
            print(f"      s{state_idx}: {f}")

    return global_formulas, local_formulas
