test: venv clean
	.venv/bin/python -m pytest -vv -s tests.py

repl: venv
	.venv/bin/python

venv: .venv/bin/activate

.venv/bin/activate: requirements-dev.txt
	test -d .venv || python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-dev.txt
	touch .venv/bin/activate

# Run the tests, compute test coverage, and open the coverage report.
coverage: venv clean
	.venv/bin/coverage run -m pytest -vv -s tests.py \
		&& .venv/bin/coverage report \
		&& .venv/bin/coverage html
	open "htmlcov/index.html"

# Remove random debris left around by python, pytest, and coverage.
clean:
	@echo "Removing generated files."
	@rm -rf \
		__pycache__ \
		.coverage \
		.pytest_cache \
		**/__pycache__ \
		**/*.pyc \
		docs/_build/* \
		dist \
		htmlcov \
		MANIFEST \
		*.egg-info

# Build the documentation.
docs:
	.venv/bin/python -m exemplary --paths "**/*.md" --render

# How to publish a release:
# - Update __version__ in outsourcer.py.
# - Commit / merge to "main" branch.
# - Run:
#   - make tag
#   - make upload_test
#   - make upload_real

tag: clean
	$(eval VERSION=$(shell sed -n -E \
		"s/^__version__ = [\'\"]([^\'\"]+)[\'\"]$$/\1/p" \
		outsourcer.py))
	@echo Tagging version $(VERSION)
	git tag -a $(VERSION) -m "Version $(VERSION)"
	git push origin $(VERSION)

# Build the distribution.
dist: clean
	rm -rf dist/
	python3 setup.py sdist
	twine check dist/*

# Upload the library to pypitest.
upload_test: dist
	twine upload --repository pypitest dist/*

# Upload the library to pypi.
upload_real: dist
	twine upload --repository pypi dist/*

.PHONY: clean coverage dist tag test upload_real upload_test
