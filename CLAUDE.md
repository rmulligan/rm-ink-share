# Pi Share Receiver Project Guidelines

## Commands
- Run server: `python app/server.py`
- Activate virtualenv: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run single test: `python -m unittest tests/test_file.py::TestClass::test_method`
- Run all tests: `python -m unittest discover tests`

## Code Style Guidelines
- **Imports**: Standard library first, then third-party packages, then local modules
- **Type Annotations**: Use type hints where applicable with comments for untyped libraries (`# type: ignore`)
- **Error Handling**: Use proper exception handling with specific exception types
- **Naming Conventions**: 
  - Variables/functions: snake_case
  - Classes: PascalCase
  - Constants: UPPER_SNAKE_CASE
- **Path Management**: Use `os.path.join()` for paths, ensure directories exist with `os.makedirs(dir, exist_ok=True)`
- **JSON Handling**: Wrap JSON operations in try/except blocks
- **Endpoint Structure**: Follow RESTful principles for API endpoints
- **Configuration**: Keep configuration variables at the top of files with UPPER_SNAKE_CASE names
- **Comments**: Use docstrings for functions and classes, inline comments for complex logic
- **Logging**: Use Python's logging module instead of print statements in production code