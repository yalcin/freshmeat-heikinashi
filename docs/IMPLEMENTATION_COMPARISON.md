# Implementation Comparison

This document compares three Heikin-Ashi implementations available in the Python trading ecosystem. All three produce **identical numerical results** — the difference is purely in performance.

## Implementations

### 1. qtpylib (vendored in freqtrade/technical)

**Source:** `technical.vendor.qtpylib.indicators.heikinashi`

```python
def heikinashi(bars):
    bars = bars.copy()
    bars["ha_close"] = (bars["open"] + bars["high"] + bars["low"] + bars["close"]) / 4

    bars.at[0, "ha_open"] = (bars.at[0, "open"] + bars.at[0, "close"]) / 2
    for i in range(1, len(bars)):
        bars.at[i, "ha_open"] = (bars.at[i - 1, "ha_open"] + bars.at[i - 1, "ha_close"]) / 2

    bars["ha_high"] = bars.loc[:, ["high", "ha_open", "ha_close"]].max(axis=1)
    bars["ha_low"] = bars.loc[:, ["low", "ha_open", "ha_close"]].min(axis=1)
    return pd.DataFrame(...)
```

**Approach:** Python `for` loop with `DataFrame.at[]` scalar accessor.

**Performance bottlenecks:**
- `DataFrame.at[]` has per-access overhead (label lookup, type checking) on every iteration.
- `DataFrame.copy()` duplicates the entire input upfront.
- `pd.concat` + `.max(axis=1)` for high/low creates intermediate DataFrames.

---

### 2. technical.candles (freqtrade/technical)

**Source:** `technical.candles.heikinashi`

```python
def heikinashi(bars):
    bars = bars.copy()
    bars.loc[:, "ha_close"] = bars.loc[:, ["open", "high", "low", "close"]].mean(axis=1)

    ha_open = [(bars.open[0] + bars.close[0]) / 2]
    [ha_open.append((ha_open[x] + bars.ha_close[x]) / 2) for x in range(0, len(bars) - 1)]
    bars["ha_open"] = ha_open

    bars.loc[:, "ha_high"] = bars.loc[:, ["high", "ha_open", "ha_close"]].max(axis=1)
    bars.loc[:, "ha_low"] = bars.loc[:, ["low", "ha_open", "ha_close"]].min(axis=1)
    result = pd.DataFrame(...)

    # Also computes: flat_bottom, flat_top, small_body, candle, reversal, wicks
    result["flat_bottom"] = np.vectorize(_flat_bottom)(...)
    ...
    return result
```

**Approach:** Python list comprehension with `list.append()` for `ha_open`, then assigns to DataFrame.

**Performance characteristics:**
- List comprehension is faster than `DataFrame.at[]` loop (~3-5x).
- Still pure Python — no JIT compilation.
- Extra overhead: computes 7 additional helper columns (`flat_bottom`, `flat_top`, `small_body`, `candle`, `reversal`, `lower_wick`, `upper_wick`) via `np.vectorize`, which is itself a Python loop wrapper.
- Uses `scipy.ndimage.shift` for reversal detection — an external dependency for a trivial shift.
- `DataFrame.copy()` + `.loc` accessor overhead.

---

### 3. freshmeat-heikinashi (this project)

**Source:** `freshmeat_heikinashi.core`

```python
@njit(cache=True)
def _heikinashi_arrays(open_, high, low, close):
    n = len(open_)
    ha_open = np.empty(n, dtype=np.float64)
    ha_high = np.empty(n, dtype=np.float64)
    ha_low = np.empty(n, dtype=np.float64)
    ha_close = np.empty(n, dtype=np.float64)

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
```

**Approach:** Numba `@njit` compiled loop over raw NumPy arrays.

**Why it's fast:**
- **No Python interpreter overhead.** Numba compiles the function to native machine code via LLVM at first call.
- **No pandas overhead.** Operates on raw `float64` arrays — no label lookups, no type checks, no DataFrame copies.
- **Cache-friendly memory access.** Sequential array traversal with `np.empty` pre-allocation.
- **`cache=True`** persists the compiled code to disk — subsequent imports skip JIT compilation.
- **All four components computed in a single pass** — no intermediate DataFrames.

**Trade-off:**
- First call incurs ~200ms JIT compilation cost (cached after that).
- Requires Numba as a dependency (~30MB).

## Design differences

| Feature | qtpylib | technical.candles | freshmeat-heikinashi |
|---|---|---|---|
| Loop mechanism | `DataFrame.at[]` | `list.append()` | Numba `@njit` |
| Data structure | DataFrame | DataFrame + list | NumPy arrays |
| DataFrame copy | Yes | Yes | No |
| Extra columns | No | 7 (flat_top, candle, etc.) | No |
| Input validation | No | No | Yes |
| Type hints | No | No | Yes (PEP 561) |
| Dependencies | pandas | pandas, numpy, scipy | pandas, numpy, numba |

## Benchmark results

Tested on AMD Ryzen / Linux, Python 3.13, pytest-benchmark (best-of-N):

### 1,000 rows

| Implementation | Min time | vs numba |
|---|---|---|
| **freshmeat-heikinashi** | **62 µs** | 1x |
| technical.candles | 10.6 ms | 171x slower |
| qtpylib | 42.8 ms | 690x slower |

### 10,000 rows

| Implementation | Min time | vs numba |
|---|---|---|
| **freshmeat-heikinashi** | **96 µs** | 1x |
| technical.candles | 79.1 ms | 827x slower |
| qtpylib | 491 ms | 5,100x slower |

### 100,000 rows

| Implementation | Min time | vs numba |
|---|---|---|
| **freshmeat-heikinashi** | **2.5 ms** | 1x |
| technical.candles | 867 ms | 343x slower |
| qtpylib | 4,619 ms | 1,830x slower |

### Scaling characteristics

- **freshmeat-heikinashi:** Near-linear scaling. 100x more data = ~40x more time (sub-linear due to fixed overhead dominating at small sizes).
- **technical.candles:** Linear scaling with high constant factor from pandas overhead.
- **qtpylib:** Linear scaling with the highest constant factor — `DataFrame.at[]` per-iteration cost is significantly worse than `list.append()`.

## Correctness verification

All three implementations produce numerically identical results. This is verified in `tests/test_benchmark.py::TestCorrectnessVsTechnical`:

```python
class TestCorrectnessVsTechnical:
    def test_matches_technical_candles(self, ohlc_10k):
        numba_result = numba_heikinashi(ohlc_10k)
        tech_result = technical_heikinashi(ohlc_10k)
        pd.testing.assert_series_equal(
            numba_result["close"], tech_result["close"],
            check_names=False, atol=1e-10,
        )
        # ... all four columns checked

    def test_matches_qtpylib_vendor(self, ohlc_10k):
        numba_result = numba_heikinashi(ohlc_10k)
        qtpylib_result = qtpylib_heikinashi(ohlc_10k)
        # ... identical checks
```

## Reproducing the benchmarks

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# pytest-benchmark (grouped side-by-side comparison)
# Requires `technical` package installed
pytest tests/test_benchmark.py -v

# CLI script
python benchmarks/bench_heikinashi.py --rows 100000
```
