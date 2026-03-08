"""Comparative benchmark: freshmeat-heikinashi (Numba) vs technical/qtpylib (pure Python).

Runs with pytest-benchmark:
    pytest tests/test_benchmark.py -v
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from technical.candles import heikinashi as technical_heikinashi
from technical.vendor.qtpylib.indicators import heikinashi as qtpylib_heikinashi

from freshmeat_heikinashi import heikinashi as numba_heikinashi

# ---------------------------------------------------------------------------
# Fixtures — shared OHLC datasets
# ---------------------------------------------------------------------------


def _make_ohlc(n: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 + rng.standard_normal(n).cumsum()
    open_ = close + rng.standard_normal(n) * 0.5
    high = np.maximum(open_, close) + rng.uniform(0, 1, n)
    low = np.minimum(open_, close) - rng.uniform(0, 1, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})


@pytest.fixture
def ohlc_1k() -> pd.DataFrame:
    return _make_ohlc(1_000)


@pytest.fixture
def ohlc_10k() -> pd.DataFrame:
    return _make_ohlc(10_000)


@pytest.fixture
def ohlc_100k() -> pd.DataFrame:
    return _make_ohlc(100_000)


# ---------------------------------------------------------------------------
# Correctness — numba output must match technical/qtpylib output
# ---------------------------------------------------------------------------


class TestCorrectnessVsTechnical:
    """Verify that Numba results match the technical package exactly."""

    def test_matches_technical_candles(self, ohlc_10k: pd.DataFrame) -> None:
        numba_result = numba_heikinashi(ohlc_10k)
        tech_result = technical_heikinashi(ohlc_10k)

        pd.testing.assert_series_equal(
            numba_result["open"],
            tech_result["open"],
            check_names=False,
            atol=1e-10,
        )
        pd.testing.assert_series_equal(
            numba_result["high"],
            tech_result["high"],
            check_names=False,
            atol=1e-10,
        )
        pd.testing.assert_series_equal(
            numba_result["low"],
            tech_result["low"],
            check_names=False,
            atol=1e-10,
        )
        pd.testing.assert_series_equal(
            numba_result["close"],
            tech_result["close"],
            check_names=False,
            atol=1e-10,
        )

    def test_matches_qtpylib_vendor(self, ohlc_10k: pd.DataFrame) -> None:
        numba_result = numba_heikinashi(ohlc_10k)
        qtpylib_result = qtpylib_heikinashi(ohlc_10k)

        pd.testing.assert_series_equal(
            numba_result["open"],
            qtpylib_result["open"],
            check_names=False,
            atol=1e-10,
        )
        pd.testing.assert_series_equal(
            numba_result["high"],
            qtpylib_result["high"],
            check_names=False,
            atol=1e-10,
        )
        pd.testing.assert_series_equal(
            numba_result["low"],
            qtpylib_result["low"],
            check_names=False,
            atol=1e-10,
        )
        pd.testing.assert_series_equal(
            numba_result["close"],
            qtpylib_result["close"],
            check_names=False,
            atol=1e-10,
        )


# ---------------------------------------------------------------------------
# Benchmarks — 1k / 10k / 100k rows, grouped for side-by-side comparison
# ---------------------------------------------------------------------------


class TestBenchmarkNumba:
    """freshmeat-heikinashi (Numba JIT)."""

    def test_1k(self, benchmark, ohlc_1k: pd.DataFrame) -> None:
        numba_heikinashi(ohlc_1k)  # warmup JIT
        benchmark.group = "1k rows"
        benchmark.name = "numba"
        benchmark(numba_heikinashi, ohlc_1k)

    def test_10k(self, benchmark, ohlc_10k: pd.DataFrame) -> None:
        numba_heikinashi(ohlc_10k)
        benchmark.group = "10k rows"
        benchmark.name = "numba"
        benchmark(numba_heikinashi, ohlc_10k)

    def test_100k(self, benchmark, ohlc_100k: pd.DataFrame) -> None:
        numba_heikinashi(ohlc_100k)
        benchmark.group = "100k rows"
        benchmark.name = "numba"
        benchmark(numba_heikinashi, ohlc_100k)


class TestBenchmarkTechnical:
    """technical.candles.heikinashi (list comprehension + pandas)."""

    def test_1k(self, benchmark, ohlc_1k: pd.DataFrame) -> None:
        benchmark.group = "1k rows"
        benchmark.name = "technical"
        benchmark(technical_heikinashi, ohlc_1k)

    def test_10k(self, benchmark, ohlc_10k: pd.DataFrame) -> None:
        benchmark.group = "10k rows"
        benchmark.name = "technical"
        benchmark(technical_heikinashi, ohlc_10k)

    def test_100k(self, benchmark, ohlc_100k: pd.DataFrame) -> None:
        benchmark.group = "100k rows"
        benchmark.name = "technical"
        benchmark(technical_heikinashi, ohlc_100k)


class TestBenchmarkQtpylib:
    """technical.vendor.qtpylib.indicators.heikinashi (for loop + .at accessor)."""

    def test_1k(self, benchmark, ohlc_1k: pd.DataFrame) -> None:
        benchmark.group = "1k rows"
        benchmark.name = "qtpylib"
        benchmark(qtpylib_heikinashi, ohlc_1k)

    def test_10k(self, benchmark, ohlc_10k: pd.DataFrame) -> None:
        benchmark.group = "10k rows"
        benchmark.name = "qtpylib"
        benchmark(qtpylib_heikinashi, ohlc_10k)

    def test_100k(self, benchmark, ohlc_100k: pd.DataFrame) -> None:
        benchmark.group = "100k rows"
        benchmark.name = "qtpylib"
        benchmark(qtpylib_heikinashi, ohlc_100k)
