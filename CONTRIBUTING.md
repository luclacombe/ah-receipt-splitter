# Contributing

Thanks for your interest in contributing to AH Receipt Splitter!

## Development Setup

```bash
# Clone and create virtual environment
git clone https://github.com/luclacombe/ah-receipt-splitter.git
cd ah-receipt-splitter
python -m venv .venv && source .venv/bin/activate

# Install all dependencies (production + dev)
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run the app
streamlit run app.py
```

## Running Tests

```bash
make test       # or: pytest tests/ -v
```

## Linting

```bash
make lint       # or: ruff check . && ruff format --check .
```

Auto-fix lint issues:

```bash
make format     # or: ruff check --fix . && ruff format .
```

## Code Style

- **Python 3.11+** with type hints on all function signatures
- **Ruff** for linting and formatting (configured in `pyproject.toml`)
- Keep functions focused — one clear responsibility each
- Docstrings on all public functions

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run `make lint && make test` to verify
5. Commit with a clear message
6. Open a Pull Request

## Adding a New Language

1. Add a new key (e.g. `"de"`) to `UI_STRINGS` in `i18n.py`
2. Add matching key to `REPORT_STRINGS` in `i18n.py`
3. Add a language card in `components/language.py`
4. Test the full flow

## Reporting Issues

Please open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
