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

Or call uv directly with the checked-in configuration:
`UV_CONFIG_FILE=uv.toml uv run pytest tests/test_cleanups.py`,
`UV_CONFIG_FILE=uv.toml uv add --exclude-newer "14 days" some-package`, or
`UV_CONFIG_FILE=uv.toml uv run python -m flowmark`.

<!-- BEGIN TBD INTEGRATION format=f08 surface=agents-md -->
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
- Fast Rust port (recommended): `uvx --from flowmark-rs==0.4.0 flowmark`.
- Python build (library / newest patch): `uvx --from flowmark==0.8.0 flowmark`.

<!-- END FLOWMARK INTEGRATION -->

## Template Maintenance

This project was built from
[simple-modern-uv](https://github.com/jlevy/simple-modern-uv).
Routine project work uses the instructions above; do not fetch the upstream template for
every task.

For toolchain changes, selective adoption of another template feature, or a Copier
update, use the portable
[simple-modern-uv skill](https://github.com/jlevy/simple-modern-uv/tree/main/skills/simple-modern-uv).
It preserves project-specific choices and distinguishes selective changes from full
template management.
`.copier-answers.yml` records this project’s update lineage.
