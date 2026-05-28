<!-- Generated from docs/shared/flowmark-readme-shared.md via
scripts/generate-python-readme.py.
-->

# flowmark

[![Follow @ojoshe on X](https://img.shields.io/badge/follow_%40ojoshe-black?logo=x&logoColor=white)](https://x.com/ojoshe)
[![CI](https://github.com/jlevy/flowmark/actions/workflows/ci.yml/badge.svg)](https://github.com/jlevy/flowmark/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/flowmark)](https://pypi.org/project/flowmark/)
[![Python versions](https://img.shields.io/pypi/pyversions/flowmark)](https://pypi.org/project/flowmark/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## Python and Rust Flowmark

> [!TIP]
> This repository is the Python reference implementation of Flowmark.
> For the fastest CLI (a single native binary, 50x+ faster), use the auto-synced Rust
> port: [flowmark-rs](https://github.com/jlevy/flowmark-rs).

## Installing Flowmark

The simplest way to install either version is with
[uv](https://github.com/astral-sh/uv).

**Python Flowmark:** Run with `uvx flowmark --help` or install it as a tool:

```shell
uv tool install --upgrade flowmark
```

**Rust Flowmark:** Run with `uvx flowmark-rs --help` or install it as a tool:

```shell
uv tool install --upgrade flowmark-rs
```

Then usage is the same:

```shell
flowmark --help
```

For use in Python projects, add the [`flowmark`](https://pypi.org/project/flowmark/)
package via uv, poetry, or pip.

**Primary command:** the `flowmark` command points to the Rust or Python version,
depending on which is first in your path.
Each package also adds a `flowmark-py` or `flowmark-rs` command.

See [flowmark-rs](https://github.com/jlevy/flowmark-rs) for more on the Rust port.

* * *

{{ shared_docs_body }}
