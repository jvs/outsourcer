# Run tests
test: clean
    uv run pytest -vv -s tests.py

# Run tests with coverage report
coverage: clean
    uv run coverage run -m pytest -vv -s tests.py
    uv run coverage report
    uv run coverage html
    open "htmlcov/index.html"

# Start Python REPL
repl:
    uv run python

# Install/sync dependencies
sync:
    uv sync

# Generate documentation from markdown files
docs:
    uv run python -m exemplary --paths "**/*.md" --render

# Run ruff linter
lint:
    uv run ruff check .

# Run ruff formatter
format:
    uv run ruff format .

# Clean generated files and cache
clean:
    rm -rf __pycache__ .coverage .pytest_cache **/__pycache__ **/*.pyc docs/_build/* dist htmlcov MANIFEST *.egg-info

# Build distribution
dist: clean
    rm -rf dist/
    uv build
    uv run twine check dist/*

# How to publish a release:
# - Update __version__ in outsourcer.py.
# - Commit / merge to "main" branch.
# - Run:
#   - just tag
#   - just upload_test
#   - just upload_real

# Tag version (extract from outsourcer.py)
tag: clean
    #!/usr/bin/env bash
    VERSION=$(sed -n -E "s/^__version__ = ['\"]([^'\"]+)['\"]$/\1/p" outsourcer.py)
    echo "Tagging version $VERSION"
    git tag -a "$VERSION" -m "Version $VERSION"
    git push origin "$VERSION"

# Upload the library to pypitest.
upload_test: dist
    twine upload --repository pypitest dist/*

# Upload the library to pypi.
upload_real: dist
    twine upload --repository pypi dist/*
