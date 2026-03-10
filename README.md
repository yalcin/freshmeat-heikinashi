# freshmeat-heikinashi

Fast Heikin-Ashi candle computation with Numba JIT acceleration.

A drop-in replacement for `technical.candles.heikinashi()` and `qtpylib.indicators.heikinashi()` — same formula, **hundreds to thousands of times faster**.

## Why?

The standard Heikin-Ashi implementations in the Python trading ecosystem use pure-Python `for` loops or list comprehensions over pandas DataFrames. The recursive nature of `ha_open` (each bar depends on the previous bar) makes vectorization impossible with plain NumPy/pandas.

**freshmeat-heikinashi** solves this by compiling the loop with [Numba](https://numba.pydata.org/) JIT, achieving native-code speed while keeping a pure-Python API.

## Installation

```bash
pip install freshmeat-heikinashi
```

**Requirements:** Python 3.10+, NumPy, pandas, Numba.

## Usage

### DataFrame API

```python
from freshmeat_heikinashi import heikinashi

ha = heikinashi(df)  # df must have open/high/low/close columns
# Returns a new DataFrame with HA open/high/low/close
```

### NumPy array API

```python
from freshmeat_heikinashi import heikinashi_arrays

ha_open, ha_high, ha_low, ha_close = heikinashi_arrays(
    open_prices, high_prices, low_prices, close_prices,
)
```

### Freqtrade strategy

```python
from freshmeat_heikinashi import heikinashi

class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        ha = heikinashi(dataframe)
        dataframe["ha_open"] = ha["open"]
        dataframe["ha_high"] = ha["high"]
        dataframe["ha_low"] = ha["low"]
        dataframe["ha_close"] = ha["close"]
        return dataframe
```

## Correctness

Output is verified to be **bit-identical** (within `1e-10` tolerance) to both `technical.candles.heikinashi()` and `qtpylib.indicators.heikinashi()` across 1k, 10k, and 100k row datasets:

```bash
pytest tests/test_benchmark.py -k "TestCorrectnessVsTechnical" -v
```

## Benchmark

Latest local `pytest-benchmark` result on 100,000 OHLC rows (min time):

| Implementation | Min time | Relative |
|---|---|---|
| **freshmeat-heikinashi** (Numba) | **1.65 ms** | 1x |
| `technical.candles.heikinashi` (list comp) | 423.50 ms | 256x slower |
| `qtpylib.indicators.heikinashi` (for loop) | 2,239.60 ms | 1,354x slower |

The absolute values are machine-dependent, but the speedup pattern is consistent.

Run the benchmarks yourself:

```bash
# pytest-benchmark (grouped comparison)
pytest tests/test_benchmark.py -v

# CLI script
python benchmarks/bench_heikinashi.py --rows 100000
```

## Documentation

- [Heikin-Ashi Formula](docs/HEIKIN_ASHI_FORMULA.md) — step-by-step formula explanation with worked example, lookahead safety analysis.
- [Implementation Comparison](docs/IMPLEMENTATION_COMPARISON.md) — detailed source code comparison of qtpylib, technical.candles, and freshmeat-heikinashi with full benchmark tables.

## Status

> **Experimental.** This project is under active development. The API may change without notice between minor versions until 1.0.

## Disclaimer

This software is provided for **educational and research purposes only**. It is not financial advice. The authors make no guarantees regarding the accuracy, reliability, or suitability of this software for any particular purpose, including but not limited to live trading.

**Use at your own risk.** The authors accept no responsibility or liability for any financial losses, trading losses, damages, or other consequences — direct or indirect — arising from the use of this software. This includes, without limitation, any commercial or trading losses incurred through live, paper, or backtested trading operations. Always validate outputs independently before making any trading decisions.

## License

[Apache License 2.0](LICENSE)
