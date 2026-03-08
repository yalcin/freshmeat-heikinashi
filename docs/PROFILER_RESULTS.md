# Profiler Results

`cProfile` output for each Heikin-Ashi implementation on **50,000 OHLC rows**. These results show *where* time is spent, not just how much — revealing the fundamental performance characteristics of each approach.

**Environment:** Python 3.13, pandas 2.x, numba 0.58+, Linux.

---

## 1. qtpylib vendor (`technical.vendor.qtpylib.indicators.heikinashi`)

**Total: 2.569 seconds — 7,656,785 function calls**

```
ncalls   tottime  cumtime  function
─────────────────────────────────────────────────────────────────
     1    0.061    2.569   indicators.py:101(heikinashi)
100000    0.065    1.683   indexing.py:2569(__getitem__)          ← .at[] read
100000    0.065    1.567   indexing.py:2519(__getitem__)          ← .at[] read (inner)
100000    0.092    1.487   frame.py:4202(_get_value)             ← scalar lookup per row
100008    0.101    1.285   frame.py:4637(_get_item_cache)        ← column cache lookup
100008    0.070    1.079   frame.py:3994(_ixs)                   ← positional indexing
 50000    0.076    0.788   indexing.py:2578(__setitem__)          ← .at[] write
 50000    0.087    0.613   indexing.py:2530(__setitem__)          ← .at[] write (inner)
 50000    0.051    0.466   frame.py:4551(_set_value)             ← scalar assignment per row
400041    0.223    0.223   generic.py:6323(__setattr__)           ← attribute overhead
```

### Analysis

The `for` loop runs 50,000 iterations. Each iteration:
- **2 reads** via `DataFrame.at[i, col]` → `_get_value` → `_ixs` → column cache
- **1 write** via `DataFrame.at[i, col]` → `_set_value` → `column_setitem`

This means **150,000 pandas internal function calls** per loop, each involving label resolution, type checking, and cache management. The actual arithmetic (`+` and `/`) takes negligible time — virtually all 2.5 seconds are spent navigating pandas internals.

---

## 2. technical.candles (`technical.candles.heikinashi`)

**Total: 0.551 seconds — 2,612,542 function calls**

```
ncalls   tottime  cumtime  function
─────────────────────────────────────────────────────────────────
     1    0.025    0.551   candles.py:6(heikinashi)
 50101    0.023    0.276   generic.py:6306(__getattr__)           ← bars.ha_close[x] attr lookup
 50029    0.057    0.155   frame.py:4073(__getitem__)             ← column access in loop
 50001    0.041    0.141   series.py:1107(__getitem__)            ← bars.ha_close[x] indexing
     7    0.008    0.081   _function_base_impl.py:2509(_call_as_normal)  ← np.vectorize calls
     7    0.029    0.073   _function_base_impl.py:2615(_vectorize_call)  ← vectorize internals
 50001    0.024    0.059   series.py:1232(_get_value)             ← scalar value extraction
```

### Analysis

The list comprehension approach avoids `DataFrame.at[]` overhead by using `list.append()`. However:

- **`bars.ha_close[x]`** triggers `__getattr__` → `__getitem__` → `_get_value` on each iteration — still 50,000 pandas attribute lookups.
- **`np.vectorize`** for the 7 extra columns (flat_top, candle, reversal, etc.) is not true vectorization — it's a Python `for` loop wrapper adding ~80ms.
- **4.7x faster than qtpylib** but still 550x slower than Numba.

---

## 3. freshmeat-heikinashi (`freshmeat_heikinashi.heikinashi`)

**Total: 0.001 seconds — 487 function calls**

```
ncalls  tottime  cumtime  function
─────────────────────────────────────────────────────────────────
     1    0.000    0.001   core.py:106(heikinashi)               ← total entry point
     1    0.000    0.000   frame.py:698(__init__)                 ← output DataFrame creation
     1    0.000    0.000   construction.py:423(dict_to_mgr)      ← DataFrame internals
     1    0.000    0.000   core.py:58(heikinashi_arrays)          ← validation wrapper
     4    0.000    0.000   frame.py:4073(__getitem__)             ← 4x column extraction
     4    0.000    0.000   series.py:792(values)                  ← .values access
```

### Analysis

The entire computation completes in **~1ms** with only **487 function calls** total:

- **4 column reads** (`df["open"].values` etc.) — extract raw NumPy arrays from the input DataFrame.
- **1 Numba kernel call** — the actual HA computation. Invisible to cProfile because it runs as compiled machine code. The loop executes entirely within LLVM-compiled native code with zero Python interpreter involvement.
- **1 DataFrame construction** — wrap the 4 result arrays back into a DataFrame.

No per-row function calls. No pandas indexing overhead. No intermediate allocations.

---

## Summary

| Metric | qtpylib | technical.candles | freshmeat-heikinashi |
|---|---|---|---|
| **Total time** | 2,569 ms | 551 ms | 1 ms |
| **Function calls** | 7,656,785 | 2,612,542 | 487 |
| **Calls per row** | ~153 | ~52 | ~0.01 |
| **Bottleneck** | `DataFrame.at[]` r/w | `Series.__getitem__` | DataFrame construction |
| **Time in pandas internals** | ~99% | ~90% | ~50% |
| **Time in actual math** | <1% | <1% | ~50% |

### Key insight

In qtpylib and technical.candles, **less than 1% of execution time is spent on the actual Heikin-Ashi arithmetic**. The rest is pandas overhead: label lookups, type checks, cache management, attribute resolution, and object creation — repeated tens of thousands of times.

freshmeat-heikinashi eliminates this entirely by operating on raw arrays and executing the loop as compiled machine code.

---

## Reproducing

```bash
cd freshmeat-heikinashi

python -c "
import cProfile
import numpy as np
import pandas as pd
from freshmeat_heikinashi import heikinashi

rng = np.random.default_rng(42)
n = 50_000
close = 100.0 + rng.standard_normal(n).cumsum()
open_ = close + rng.standard_normal(n) * 0.5
high = np.maximum(open_, close) + rng.uniform(0, 1, n)
low = np.minimum(open_, close) - rng.uniform(0, 1, n)
df = pd.DataFrame({'open': open_, 'high': high, 'low': low, 'close': close})

heikinashi(df)  # warmup JIT
cProfile.run('heikinashi(df)', sort='cumulative')
"
```
