# LeRobot Project Guidelines

## Build/Run Commands
- Install: `uv sync --extra dev --extra test` or `uv pip install -e .`
- Run main: `python main.py`
- Training: `python scripts/train.py`
- Evaluation: `python scripts/eval.py`
- Visualize dataset: `python scripts/visualize_dataset.py` or `python scripts/visualize_dataset_html.py`

## Test Commands
- Run all tests: `python -m pytest -sv ./tests` 
- Run specific test: `pytest tests/path/to/test_file.py::test_function`
- End-to-end tests: `make test-end-to-end`

## Lint Commands
- Setup: `pre-commit install`
- Run on staged files: `pre-commit`
- Run on all files: `pre-commit run --all-files`

## Code Style Guidelines
- **Line Length**: 110 characters maximum
- **Imports**: Standard library first, third-party packages next, local imports last
- **Naming**: Classes=PascalCase, functions/variables=snake_case, constants=UPPER_SNAKE_CASE
- **Type Annotations**: Required for all function parameters and return values
- **Docstrings**: Google-style with Args, Returns, Raises sections; include examples for complex functions
- **Error Handling**: Use descriptive error messages; create custom exceptions when appropriate
- **Structure**: Follow modular architecture with factory pattern for object creation
- **Best Practices**: 
  - Use absolute imports within the project
  - Prefix private methods/variables with underscore
  - Use dataclasses for structured data
  - Include meaningful log messages
  - Target Python 3.10+ compatibility