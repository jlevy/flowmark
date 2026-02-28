---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $TRYSCRIPT_GIT_ROOT/.venv/bin
before: |
  cp -r $TRYSCRIPT_TEST_DIR/fixtures/. fixtures/
---

# File Discovery Tests

Tests for --list-files, extend-include, extend-exclude, gitignore, flowmarkignore,
max-size, force-exclude, and glob patterns using the project/ fixture tree.

## D1: List files in directory finds md files

```console
$ flowmark --list-files fixtures/project/ | xargs -I{} basename {} | sort
README.md
README.md
api.md
file.md
guide.md
tutorial.md
wip.md
```

## D2: Default dirs excluded (node_modules, .venv, build, vendor, .git)

```console
$ flowmark --list-files fixtures/project/ | grep -c node_modules
? 1
0
```

```console
$ flowmark --list-files fixtures/project/ | grep -c '\.venv'
? 1
0
```

```console
$ flowmark --list-files fixtures/project/ | grep -c build/
? 1
0
```

```console
$ flowmark --list-files fixtures/project/ | grep -c vendor/
? 1
0
```

## D3: Extend include adds MDX files

```console
$ flowmark --list-files --extend-include "*.mdx" fixtures/project/ | xargs -I{} basename {} | sort
README.md
README.md
about.mdx
api.md
file.md
guide.md
index.mdx
tutorial.md
wip.md
```

## D4: Extend exclude removes drafts

```console
$ flowmark --list-files --extend-exclude "drafts/" fixtures/project/ | xargs -I{} basename {} | sort
README.md
README.md
api.md
file.md
guide.md
tutorial.md
```

## D5: Force exclude applies exclusion patterns to explicitly named files

```console
$ flowmark --list-files --force-exclude fixtures/project/node_modules/pkg/README.md | wc -l | tr -d ' '
0
```

## D6: Without force-exclude, explicitly named excluded files pass through

```console
$ flowmark --list-files fixtures/project/node_modules/pkg/README.md | xargs -I{} basename {}
README.md
```

## D7: Files max size filters large files

```console
$ dd if=/dev/zero of=fixtures/project/big.md bs=1024 count=2048 2>/dev/null && flowmark --list-files --files-max-size 100 fixtures/project/ | grep -c big
? 1
0
```

## D8: Flowmarkignore excludes skip directory

```console
$ flowmark --list-files fixtures/project/ | grep -c skip/
? 1
0
```

## D9: Glob pattern expansion

```console
$ flowmark --list-files "fixtures/project/docs/*.md" | xargs -I{} basename {} | sort
api.md
guide.md
tutorial.md
```

## D10: Single explicit file

```console
$ flowmark --list-files fixtures/project/README.md | xargs -I{} basename {}
README.md
```

## D11: Exclude replaces defaults

With `--exclude`, defaults are replaced rather than extended.
Excluding only `docs/` therefore includes paths normally excluded by defaults.

```console
$ flowmark --list-files --exclude "docs/" fixtures/project/ | xargs -I{} basename {} | sort
README.md
README.md
README.md
README.md
file.md
lib.md
output.md
wip.md
```
