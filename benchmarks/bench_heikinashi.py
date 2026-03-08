"""Benchmark: freshmeat-heikinashi (Numba) vs technical/qtpylib (pure Python).

Usage:
    python benchmarks/bench_heikinashi.py [--rows N]
"""

from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from technical.candles import heikinashi as technical_heikinashi
from technical.vendor.qtpylib.indicators import heikinashi as qtpylib_heikinashi

from freshmeat_heikinashi import heikinashi as numba_heikinashi


def _generate_ohlc(n: int, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic OHLC DataFrame with *n* rows."""
    rng = np.random.default_rng(seed)
    close = 100.0 + rng.standard_normal(n).cumsum()
    open_ = close + rng.standard_normal(n) * 0.5
    high = np.maximum(open_, close) + rng.uniform(0, 1, n)
    low = np.minimum(open_, close) - rng.uniform(0, 1, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


def _time_fn(fn, df: pd.DataFrame, warmup: int = 1, repeat: int = 10) -> float:
    """Return best-of-*repeat* execution time in milliseconds."""
    for _ in range(warmup):
        fn(df)
    times: list[float] = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn(df)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return min(times)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Heikin-Ashi implementations")
    parser.add_argument("--rows", type=int, default=100_000, help="Number of OHLC rows")
    args = parser.parse_args()

    n = args.rows
    df = _generate_ohlc(n)

    print(f"Benchmarking with {n:,} rows")
    print("=" * 50)

    numba_ms = _time_fn(numba_heikinashi, df)
    print(f"  freshmeat-heikinashi (numba)     : {numba_ms:10.2f} ms")

    technical_ms = _time_fn(technical_heikinashi, df)
    print(f"  technical.candles (list comp)     : {technical_ms:10.2f} ms")

    qtpylib_ms = _time_fn(qtpylib_heikinashi, df)
    print(f"  qtpylib vendor (.at for loop)    : {qtpylib_ms:10.2f} ms")

    print()
    print(f"  Speedup vs technical : {technical_ms / numba_ms:,.1f}x")
    print(f"  Speedup vs qtpylib   : {qtpylib_ms / numba_ms:,.1f}x")


if __name__ == "__main__":
    main()
