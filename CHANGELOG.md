# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-08

### Added

- `heikinashi()` — DataFrame API for Heikin-Ashi candle computation.
- `heikinashi_arrays()` — low-level NumPy array API.
- Numba JIT-compiled kernel (`@njit(cache=True)`) for the recursive HA loop.
- Input validation: empty arrays, mismatched lengths, missing columns.
- PEP 561 `py.typed` marker for type checker support.
- Correctness tests against `technical.candles.heikinashi` and `qtpylib.indicators.heikinashi`.
- Comparative benchmarks (pytest-benchmark + CLI script).
