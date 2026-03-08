"""Tests for Heikin-Ashi computation correctness."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from freshmeat_heikinashi import heikinashi, heikinashi_arrays

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ohlc() -> pd.DataFrame:
    """Small deterministic OHLC dataset."""
    return pd.DataFrame(
        {
            "open": [10.0, 11.0, 12.0, 11.5, 13.0],
            "high": [12.0, 13.0, 14.0, 13.5, 15.0],
            "low": [9.0, 10.0, 11.0, 10.5, 12.0],
            "close": [11.0, 12.0, 13.0, 12.5, 14.0],
        }
    )


def _reference_heikinashi(df: pd.DataFrame) -> pd.DataFrame:
    """Pure-Python reference implementation for verification."""
    n = len(df)
    ha_open = np.empty(n)
    ha_high = np.empty(n)
    ha_low = np.empty(n)
    ha_close = np.empty(n)

    o, h, low, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values

    ha_close[0] = (o[0] + h[0] + low[0] + c[0]) / 4.0
    ha_open[0] = (o[0] + c[0]) / 2.0
    ha_high[0] = max(h[0], ha_open[0], ha_close[0])
    ha_low[0] = min(low[0], ha_open[0], ha_close[0])

    for i in range(1, n):
        ha_close[i] = (o[i] + h[i] + low[i] + c[i]) / 4.0
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0
        ha_high[i] = max(h[i], ha_open[i], ha_close[i])
        ha_low[i] = min(low[i], ha_open[i], ha_close[i])

    return pd.DataFrame(
        {"open": ha_open, "high": ha_high, "low": ha_low, "close": ha_close},
        index=df.index,
    )


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------


class TestHeikinashiDataFrame:
    """Tests for the DataFrame API."""

    def test_matches_reference(self, sample_ohlc: pd.DataFrame) -> None:
        result = heikinashi(sample_ohlc)
        expected = _reference_heikinashi(sample_ohlc)
        pd.testing.assert_frame_equal(result, expected)

    def test_preserves_index(self, sample_ohlc: pd.DataFrame) -> None:
        sample_ohlc.index = pd.date_range("2024-01-01", periods=len(sample_ohlc), freq="h")
        result = heikinashi(sample_ohlc)
        pd.testing.assert_index_equal(result.index, sample_ohlc.index)

    def test_output_columns(self, sample_ohlc: pd.DataFrame) -> None:
        result = heikinashi(sample_ohlc)
        assert list(result.columns) == ["open", "high", "low", "close"]

    def test_ha_high_ge_open_close(self, sample_ohlc: pd.DataFrame) -> None:
        result = heikinashi(sample_ohlc)
        assert (result["high"] >= result["open"]).all()
        assert (result["high"] >= result["close"]).all()

    def test_ha_low_le_open_close(self, sample_ohlc: pd.DataFrame) -> None:
        result = heikinashi(sample_ohlc)
        assert (result["low"] <= result["open"]).all()
        assert (result["low"] <= result["close"]).all()

    def test_single_bar(self) -> None:
        df = pd.DataFrame(
            {
                "open": [100.0],
                "high": [110.0],
                "low": [90.0],
                "close": [105.0],
            }
        )
        result = heikinashi(df)
        assert result["close"].iloc[0] == pytest.approx(101.25)
        assert result["open"].iloc[0] == pytest.approx(102.5)

    def test_extra_columns_ignored(self, sample_ohlc: pd.DataFrame) -> None:
        sample_ohlc["volume"] = 1000
        result = heikinashi(sample_ohlc)
        assert "volume" not in result.columns

    def test_does_not_mutate_input(self, sample_ohlc: pd.DataFrame) -> None:
        original = sample_ohlc.copy()
        heikinashi(sample_ohlc)
        pd.testing.assert_frame_equal(sample_ohlc, original)


class TestHeikinashiArrays:
    """Tests for the low-level NumPy array API."""

    def test_matches_dataframe_api(self, sample_ohlc: pd.DataFrame) -> None:
        ha_open, ha_high, ha_low, ha_close = heikinashi_arrays(
            sample_ohlc["open"].values,
            sample_ohlc["high"].values,
            sample_ohlc["low"].values,
            sample_ohlc["close"].values,
        )
        df_result = heikinashi(sample_ohlc)
        np.testing.assert_array_almost_equal(ha_open, df_result["open"].values)
        np.testing.assert_array_almost_equal(ha_high, df_result["high"].values)
        np.testing.assert_array_almost_equal(ha_low, df_result["low"].values)
        np.testing.assert_array_almost_equal(ha_close, df_result["close"].values)

    def test_accepts_float32_input(self) -> None:
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        ha_open, _ha_high, _ha_low, _ha_close = heikinashi_arrays(arr, arr, arr, arr)
        assert ha_open.dtype == np.float64

    def test_large_array(self) -> None:
        rng = np.random.default_rng(42)
        n = 100_000
        close = 100 + rng.standard_normal(n).cumsum()
        open_ = close + rng.standard_normal(n) * 0.5
        high = np.maximum(open_, close) + rng.uniform(0, 1, n)
        low = np.minimum(open_, close) - rng.uniform(0, 1, n)

        ha_open, ha_high, ha_low, _ha_close = heikinashi_arrays(open_, high, low, close)
        assert len(ha_open) == n
        assert np.all(ha_high >= ha_low)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for input validation."""

    def test_missing_column_raises(self) -> None:
        df = pd.DataFrame({"open": [1.0], "high": [2.0], "low": [0.5]})
        with pytest.raises(KeyError, match="close"):
            heikinashi(df)

    def test_empty_dataframe_raises(self) -> None:
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": []})
        with pytest.raises(ValueError, match="empty"):
            heikinashi(df)

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            heikinashi_arrays(
                np.array([1.0, 2.0]),
                np.array([1.0, 2.0, 3.0]),
                np.array([1.0, 2.0]),
                np.array([1.0, 2.0]),
            )

    def test_empty_arrays_raises(self) -> None:
        empty = np.array([], dtype=np.float64)
        with pytest.raises(ValueError, match="empty"):
            heikinashi_arrays(empty, empty, empty, empty)
