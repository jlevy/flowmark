<!-- Generated from docs/shared/flowmark-readme-shared.md via
scripts/generate-python-readme.py.
-->

# flowmark

[![Follow @ojoshe on X](https://img.shields.io/badge/follow_%40ojoshe-black?logo=x&logoColor=white)](https://x.com/ojoshe)
[![CI](https://github.com/jlevy/flowmark/actions/workflows/ci.yml/badge.svg)](https://github.com/jlevy/flowmark/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/flowmark)](https://pypi.org/project/flowmark/)
[![Python versions](https://img.shields.io/pypi/pyversions/flowmark)](https://pypi.org/project/flowmark/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## Original Python Flowmark

This repository is the Python reference implementation of Flowmark.

For fastest CLI usage via a single native binary, consider the auto-synced Rust port:
[flowmark-rs](https://github.com/jlevy/flowmark-rs).

## Installing Python Flowmark CLI

The simplest way to use the Python version is [uv](https://github.com/astral-sh/uv).

Run with `uvx flowmark --help` or install it as a tool:

```shell
uv tool install --upgrade flowmark
```

Then:

```shell
flowmark --help
```

For use in Python projects, add the [`flowmark`](https://pypi.org/project/flowmark/)
package via uv, poetry, or pip.

Primary command: `flowmark`. Alias available in this repo: `flowmark-py`.

* * *

{{ shared_docs_body }}
