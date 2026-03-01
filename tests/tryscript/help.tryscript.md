---
sandbox: true
env:
  NO_COLOR: "1"
  LC_ALL: C
path:
  - $TRYSCRIPT_GIT_ROOT/.venv/bin
---

# Help Output

## H1: Help tagline

```console
$ flowmark --help | grep -F "Flowmark: Better auto-formatting for Markdown and plaintext"
Flowmark: Better auto-formatting for Markdown and plaintext
```

## H2: Common usage examples are present

```console
$ flowmark --help | grep -F "flowmark --auto README.md"
  flowmark --auto README.md
```

```console
$ flowmark --help | grep -F "flowmark --auto docs/"
  flowmark --auto docs/
```

```console
$ flowmark --help | grep -F "flowmark --auto ."
  flowmark --auto .
```

```console
$ flowmark --help | grep -F "flowmark --list-files ."
  flowmark --list-files .
```

## H3: Agent guidance is explicit

```console
$ flowmark --help | grep -Fx "  flowmark --skill"
  flowmark --skill
```

```console
$ flowmark --help | grep -F "Agents should run"
  Agents should run `flowmark --skill` for full Flowmark usage guidance.
```

## H4: Full docs are via --docs

```console
$ flowmark --help | grep -F "flowmark --docs"
Use `flowmark --docs` for full documentation.
```
