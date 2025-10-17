# Tests

## Preparations

- Test dependencies are part of an optional groups within the pyproject.toml; to install please run 
  `poetry install --only tests`

- Tests will be run against python 3.10, 3.11 and 3.12; pyenv can be used to make sure all 3 of these python versions 
  are installed. Please refer to the pyenv documentation for further details.  

## Run the tests

Run `poetry run tox` to kick off the unit tests; all tests are part of the `<<repo_root_dir>>/tests` directory. 

A coverage html report is also created (`<<repo_root_dir>>/htmlcov`) which can be used to check how much of the 
code base is covered by the current tests.
