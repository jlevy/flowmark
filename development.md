## Development

[Fork](https://github.com/jlevy/kmd/fork) this repo (having your own fork will make it
easier to contribute),
[check out](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository),
and then install the package dependencies:

```shell
poetry install
```

Developer workflows:

```shell
# Run poetry install, lint, and test:
make

# Build wheel:
make build

# Linting and testing individually:
make lint
make test

# Delete all the build artifacts:
make clean

# To run a shell within the Python environment:
poetry shell
# Thereafter you can run tests.

# To run tests:
pytest   # all tests
pytest -s src/module/some_file.py  # one test, showing outputs

# Poetry dependency management commands:
# Upgrade all dependencies:
poetry up
# Update poetry itself: 
poetry self update
```

## Release Process

This project is set up to publish to [PyPI](https://pypi.org/) from GitHub Actions.

Thanks to the dynamic versioning plugin and `publish.yml` workflow, you can
simply create tagged releases on GitHub and the tag will trigger a release
build, which then uploads it to PyPI.

For this to work you will need to have a PyPI account and authorize your
repository to publish to PyPI. The simplest way to do that is on
[the publishing settings page](https://pypi.org/manage/account/publishing/).
Configure "Trusted Publisher Management" and register your GitHub repo as
a new "pending" trusted publisher, entering the project name, repo owner,
repo name, and `publish.yml` as the workflow name.