# Heikin-Ashi Formula

Heikin-Ashi ("average bar" in Japanese) is a modified candlestick charting technique that filters out market noise by averaging price data. Unlike standard OHLC candles that use raw prices, Heikin-Ashi candles are computed from the previous bar's values, producing smoother trends with fewer false signals.

## Formula

Given a standard OHLC bar at index `i`:

| Component | Formula | Nature |
|---|---|---|
| **HA Close** | `(Open[i] + High[i] + Low[i] + Close[i]) / 4` | Simple average of current bar |
| **HA Open** | `(HA_Open[i-1] + HA_Close[i-1]) / 2` | Recursive — depends on previous HA values |
| **HA High** | `max(High[i], HA_Open[i], HA_Close[i])` | Highest of real high and computed values |
| **HA Low** | `min(Low[i], HA_Open[i], HA_Close[i])` | Lowest of real low and computed values |

### First bar (seed values)

The recursion needs initial values for `i = 0`:

| Component | Seed |
|---|---|
| **HA Close[0]** | `(Open[0] + High[0] + Low[0] + Close[0]) / 4` |
| **HA Open[0]** | `(Open[0] + Close[0]) / 2` |
| **HA High[0]** | `max(High[0], HA_Open[0], HA_Close[0])` |
| **HA Low[0]** | `min(Low[0], HA_Open[0], HA_Close[0])` |

## Step-by-step example

Given 3 bars of raw OHLC data:

| Bar | Open | High | Low | Close |
|-----|------|------|-----|-------|
| 0   | 10   | 12   | 9   | 11    |
| 1   | 11   | 13   | 10  | 12    |
| 2   | 12   | 14   | 11  | 13    |

### Bar 0 (seed)

```
HA_Close[0] = (10 + 12 + 9 + 11) / 4 = 10.50
HA_Open[0]  = (10 + 11) / 2           = 10.50
HA_High[0]  = max(12, 10.50, 10.50)   = 12.00
HA_Low[0]   = min(9, 10.50, 10.50)    =  9.00
```

### Bar 1

```
HA_Close[1] = (11 + 13 + 10 + 12) / 4     = 11.50
HA_Open[1]  = (HA_Open[0] + HA_Close[0]) / 2
            = (10.50 + 10.50) / 2          = 10.50
HA_High[1]  = max(13, 10.50, 11.50)        = 13.00
HA_Low[1]   = min(10, 10.50, 11.50)        = 10.00
```

### Bar 2

```
HA_Close[2] = (12 + 14 + 11 + 13) / 4     = 12.50
HA_Open[2]  = (HA_Open[1] + HA_Close[1]) / 2
            = (10.50 + 11.50) / 2          = 11.00
HA_High[2]  = max(14, 11.00, 12.50)        = 14.00
HA_Low[2]   = min(11, 11.00, 12.50)        = 11.00
```

## Why the recursion matters for performance

`HA_Close`, `HA_High`, and `HA_Low` can all be vectorized — they only depend on current bar values. The bottleneck is `HA_Open`: each bar requires the previous bar's `HA_Open` and `HA_Close`, creating a strict sequential dependency.

This means:
- **NumPy/pandas vectorization cannot help** — you must loop.
- **Pure Python loops are slow** — interpreter overhead per iteration.
- **Numba compiles the loop to machine code** — same algorithm, native speed.

## Lookahead safety

The HA formula is lookahead-safe by construction:
- `HA_Close[i]` uses only bar `i` data.
- `HA_Open[i]` uses only bar `i-1` data.
- `HA_High[i]` and `HA_Low[i]` use bar `i` data plus the already-computed HA values.

No future data is accessed at any point. This makes Heikin-Ashi safe for backtesting.

## References

- [StockCharts — Heikin-Ashi](https://school.stockcharts.com/doku.php?id=chart_analysis:heikin_ashi)
- [Investopedia — Heikin-Ashi Technique](https://www.investopedia.com/terms/h/heikinashi.asp)
- Valcu, D. (2004). "Using The Heikin-Ashi Technique." *Technical Analysis of Stocks & Commodities*, 22(2).
