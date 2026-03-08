# Contributing to freshmeat-heikinashi

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/your-username/freshmeat-heikinashi.git
cd freshmeat-heikinashi
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

3. Install pre-commit hooks:

```bash
pre-commit install
```

## Code Standards

- **Python >= 3.10** — use modern syntax features
- **Google-style docstrings** on all public functions, classes, and methods
- **Ruff** for linting and formatting (line length: 99)
- Keep dependencies minimal — do not add new runtime dependencies without discussion

## Running Tests

```bash
# All tests (correctness + benchmarks)
pytest tests/ -v

# Correctness only (fast)
pytest tests/test_core.py -v

# Benchmarks only
pytest tests/test_benchmark.py -v

# Run a specific test
pytest tests/test_core.py::TestHeikinashiDataFrame::test_matches_reference
```

## Linting and Formatting

```bash
# Lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check --fix src/ tests/

# Format
ruff format src/ tests/

# Check formatting
ruff format --check src/ tests/
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all checks pass: `ruff check`, `ruff format --check`, `pytest`
4. Update `CHANGELOG.md` with your changes
5. Submit a pull request

## Reporting Issues

- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for bugs
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) for new features

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
