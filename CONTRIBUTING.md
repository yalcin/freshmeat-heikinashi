# Contributing

Contributions are welcome. Please follow these guidelines.

## Setup

```bash
git clone https://github.com/yalcin/freshmeat-heikinashi.git
cd freshmeat-heikinashi
pip install -e ".[dev]"
```

## Running tests

```bash
# All tests (correctness + benchmarks)
pytest tests/ -v

# Correctness only (fast)
pytest tests/test_core.py -v

# Benchmarks only
pytest tests/test_benchmark.py -v
```

## Code style

- Follow PEP 8 and PEP 257.
- Use [ruff](https://docs.astral.sh/ruff/) for linting (`ruff check .`).
- Keep dependencies minimal — do not add new runtime dependencies without discussion.

## Pull requests

1. Fork the repo and create a feature branch.
2. Add tests for any new functionality.
3. Ensure all tests pass.
4. Submit a pull request with a clear description.
