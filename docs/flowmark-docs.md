# Flowmark Documentation

Flowmark is a Markdown auto-formatter that provides enhanced text wrapping capabilities
with special handling for Markdown content.

## Installation

```bash
# Install globally with uv
uv tool install flowmark

# Or run directly without installing
uvx flowmark@latest --help

# Or install with pip
pip install flowmark
```

## Command-Line Usage

### Basic Usage

```bash
# Format a file to stdout
flowmark README.md

# Format with all auto-formatting options and edit in-place
flowmark --auto README.md

# Format multiple files in-place
flowmark --inplace README.md CHANGELOG.md docs/*.md

# Process plaintext instead of Markdown
flowmark --plaintext text.txt
```

### Input/Output Options

| Option | Description |
|--------|-------------|
| `files` | Input files (use '-' for stdin, multiple files supported) |
| `-o, --output FILE` | Output file (use '-' for stdout) |
| `-i, --inplace` | Edit file in place |
| `--nobackup` | Do not create .bak backup when using --inplace |

### Formatting Options

| Option | Description |
|--------|-------------|
| `-w, --width WIDTH` | Line width to wrap to (default: 88, use 0 to disable) |
| `-s, --semantic` | Use semantic (sentence-based) line breaks |
| `-c, --cleanups` | Enable safe cleanups for common Markdown issues |
| `--smartquotes` | Convert straight quotes to typographic curly quotes |
| `--ellipses` | Convert three dots (...) to ellipsis character (…) |
| `--list-spacing MODE` | Control list spacing: preserve, loose, or tight |
| `-p, --plaintext` | Process as plaintext (no Markdown parsing) |

### Convenience Options

| Option | Description |
|--------|-------------|
| `--auto` | Same as `--inplace --nobackup --semantic --cleanups --smartquotes --ellipses` |
| `--version` | Show version information |

### Agent Integration Options

| Option | Description |
|--------|-------------|
| `--skill` | Print skill instructions (SKILL.md content) |
| `--install-skill` | Install Claude Code skill for flowmark |
| `--agent-base DIR` | Agent config directory for skill installation (default: ~/.claude) |
| `--docs` | Print this documentation |

## Semantic Line Breaks

The `--semantic` option breaks lines at sentence boundaries instead of at fixed column
widths. This produces cleaner git diffs because editing one sentence doesn't cause
cascading line changes throughout a paragraph.

Benefits:
- Cleaner git diffs (changes isolated to affected sentences)
- Easier review of changes in pull requests
- Better readability in plain text editors
- Consistent formatting across contributors

## Smart Typography

With `--smartquotes`:
- Straight double quotes `"..."` become curly `"..."`
- Straight single quotes/apostrophes `'...'` become curly `'...'`

With `--ellipses`:
- Three consecutive dots `...` become the ellipsis character `…`

## List Spacing Control

The `--list-spacing` option controls blank lines between list items:

- `preserve` (default): Keep original tight/loose formatting
- `loose`: Add blank lines between all items
- `tight`: Remove blank lines where possible

## Library Usage

Flowmark can be used as a Python library:

```python
from flowmark import reformat_text, reformat_file, fill_markdown

# Format a string
formatted = reformat_text(
    text="Your markdown content here...",
    width=88,
    semantic=True,
    smartquotes=True,
)

# Format a file
reformat_file(
    file_path="README.md",
    output_path="README_formatted.md",
    width=88,
    semantic=True,
)

# Low-level: wrap a single paragraph
wrapped = fill_markdown(
    text="A long paragraph...",
    width=88,
    semantic_linebreaks=True,
)
```

## Examples

### Format for Git (Recommended Workflow)

```bash
# Format all Markdown files with semantic line breaks
flowmark --auto *.md

# Review the changes
git diff

# Commit if satisfied
git add -A && git commit -m "Format Markdown files"
```

### Format LLM Output

```bash
# Pipe LLM output through flowmark
echo "$llm_output" | flowmark --semantic

# Or save to file
echo "$llm_output" | flowmark --semantic -o formatted.md
```

### Batch Format Directory

```bash
# Format all .md files recursively
find . -name "*.md" -exec flowmark --auto {} \;
```

### Pipeline Integration

```bash
# Format stdin to stdout
cat document.md | flowmark --semantic > formatted.md

# Use in shell scripts
flowmark --semantic < input.md > output.md
```

## Notes

- Code blocks and inline code are never modified
- Markdown structure (headers, lists, blockquotes) is preserved
- HTML comments and raw HTML blocks are preserved
- Works with GFM (GitHub Flavored Markdown) extensions
- Uses the marko library for Markdown parsing

## Links

- Repository: https://github.com/jlevy/flowmark
- PyPI: https://pypi.org/project/flowmark/
