# Agents

For development setup, see [docs/development.md](docs/development.md).

For documentation overview, see [docs/docs-overview.md](docs/docs-overview.md).

Before adding or upgrading any dependency, read
[SUPPLY-CHAIN-SECURITY.md](SUPPLY-CHAIN-SECURITY.md) (14-day cool-off, frozen lockfile,
pinned runners).

This project uses [uv](https://docs.astral.sh/uv/) for Python and dependency management.
Use the `Makefile` for the standard workflows:

```bash
make install     # Install all locked dependency groups.
make lint-check  # Check formatting, lint, and types without modifying files.
make test        # Run pytest and golden tests.
make build       # Build wheel and sdist from the locked build group.
```

<!-- BEGIN TBD INTEGRATION format=f06 surface=agents-md -->
## tbd

This repository uses **tbd** for git-native issue tracking (beads), spec-driven
planning, and on-demand engineering guidelines.
As the agent, you operate tbd on the user’s behalf: translate their requests into tbd
actions rather than telling them to run commands.

- Run `tbd prime` to load current project state and the full tbd workflow.
- Run `tbd skill` for the complete reusable tbd skill instructions.
- Run `tbd shortcut --list` and `tbd guidelines --list` for on-demand resources.
- Track all work as beads: `tbd create`, `tbd ready`, `tbd close`, and `tbd sync`.

<!-- END TBD INTEGRATION -->

<!-- BEGIN FLOWMARK INTEGRATION format=f03 surface=agents-md -->
## flowmark

Auto-format Markdown with `flowmark` for clean, semantic git diffs.

- Run `flowmark --auto <files>` on Markdown you create or edit.
- Run `flowmark --docs` for full usage and `flowmark --skill` for the skill.
- If `flowmark` is not on `PATH`, use a pinned `uvx` runner (never `@latest`).
- Fast Rust port (recommended): `uvx --from flowmark-rs==0.3.2 flowmark`.
- Python build (library / newest patch): `uvx --from flowmark==0.7.3 flowmark`.

<!-- END FLOWMARK INTEGRATION -->
