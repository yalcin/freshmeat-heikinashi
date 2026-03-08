"""Numba-accelerated Heikin-Ashi candle computation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit


@njit(cache=True)
def _heikinashi_arrays(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute Heikin-Ashi OHLC from raw OHLC arrays.

    The recursive HA formula uses only past data — no lookahead.

    Args:
        open_: Open prices.
        high: High prices.
        low: Low prices.
        close: Close prices.

    Returns:
        Tuple of ``(ha_open, ha_high, ha_low, ha_close)`` arrays.
    """
    n = len(open_)
    ha_open = np.empty(n, dtype=np.float64)
    ha_high = np.empty(n, dtype=np.float64)
    ha_low = np.empty(n, dtype=np.float64)
    ha_close = np.empty(n, dtype=np.float64)

    # Seed first bar
    ha_close[0] = (open_[0] + high[0] + low[0] + close[0]) / 4.0
    ha_open[0] = (open_[0] + close[0]) / 2.0
    ha_high[0] = max(high[0], ha_open[0], ha_close[0])
    ha_low[0] = min(low[0], ha_open[0], ha_close[0])

    for i in range(1, n):
        ha_close[i] = (open_[i] + high[i] + low[i] + close[i]) / 4.0
        ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0
        ha_high[i] = max(high[i], ha_open[i], ha_close[i])
        ha_low[i] = min(low[i], ha_open[i], ha_close[i])

    return ha_open, ha_high, ha_low, ha_close


def heikinashi_arrays(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute Heikin-Ashi OHLC from NumPy arrays.

    Thin wrapper around the Numba-jitted kernel that validates input
    and ensures ``float64`` dtype.

    Args:
        open_: Open prices.
        high: High prices.
        low: Low prices.
        close: Close prices.

    Returns:
        Tuple of ``(ha_open, ha_high, ha_low, ha_close)`` arrays.

    Raises:
        ValueError: If arrays are empty or have mismatched lengths.
    """
    lengths = {len(open_), len(high), len(low), len(close)}
    if len(lengths) != 1:
        raise ValueError(f"All arrays must have the same length, got {sorted(lengths)}")
    if len(open_) == 0:
        raise ValueError("Arrays must not be empty")

    return _heikinashi_arrays(
        np.asarray(open_, dtype=np.float64),
        np.asarray(high, dtype=np.float64),
        np.asarray(low, dtype=np.float64),
        np.asarray(close, dtype=np.float64),
    )


def heikinashi(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert an OHLC DataFrame to Heikin-Ashi candles.

    Args:
        dataframe: Must contain ``open``, ``high``, ``low``, ``close`` columns.

    Returns:
        DataFrame with Heikin-Ashi OHLC values and the same index.

    Raises:
        KeyError: If required columns are missing.
        ValueError: If the dataframe is empty.
    """
    missing = {"open", "high", "low", "close"} - set(dataframe.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    ha_open, ha_high, ha_low, ha_close = heikinashi_arrays(
        dataframe["open"].values,
        dataframe["high"].values,
        dataframe["low"].values,
        dataframe["close"].values,
    )
    return pd.DataFrame(
        {"open": ha_open, "high": ha_high, "low": ha_low, "close": ha_close},
        index=dataframe.index,
    )
