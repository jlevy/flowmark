#!/usr/bin/env bash
set -euo pipefail

# Quality gates for Flowmark tryscript golden tests.
# Run from repository root.

EXIT_CODE=0
TESTS_DIR="tests/tryscript"

if [ ! -d "$TESTS_DIR" ]; then
  echo "ERROR: Missing $TESTS_DIR"
  exit 1
fi

echo "Checking anti-patterns..."
ELISIONS=$(grep -rn '^\.\.\.$' "$TESTS_DIR" 2>/dev/null || true)
if [ -n "$ELISIONS" ]; then
  echo "ERROR: Found bare ... elisions:"
  echo "$ELISIONS"
  EXIT_CODE=1
else
  echo "OK: no bare ... elisions"
fi

echo ""
echo "Checking path portability..."
LEGACY_PATHS=$(grep -rn 'target/debug' "$TESTS_DIR" 2>/dev/null || true)
if [ -n "$LEGACY_PATHS" ]; then
  echo "ERROR: Found Rust-specific binary paths in Python tryscript suite:"
  echo "$LEGACY_PATHS"
  EXIT_CODE=1
else
  echo "OK: no Rust-only binary paths"
fi

echo ""
echo "Checking required tryscript modules..."
REQUIRED_FILES=(
  help.tryscript.md
  errors-version.tryscript.md
  formatting.tryscript.md
  typography-tests.tryscript.md
  list-spacing.tryscript.md
  auto-mode.tryscript.md
  file-ops.tryscript.md
  stdin.tryscript.md
  file-discovery.tryscript.md
  config-interaction.tryscript.md
  verbose-docs.tryscript.md
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$TESTS_DIR/$file" ]; then
    echo "  MISSING: $file"
    EXIT_CODE=1
  else
    echo "  OK: $file"
  fi
done

echo ""
echo "Checking key CLI flag coverage..."
search_cmd_matches() {
  local regex="$1"
  if command -v rg >/dev/null 2>&1; then
    rg -n --pcre2 "$regex" "$TESTS_DIR"/*.tryscript.md 2>/dev/null || true
  else
    grep -nE "$regex" "$TESTS_DIR"/*.tryscript.md 2>/dev/null || true
  fi
}

check_cmd_pattern() {
  local label="$1"
  local regex="$2"
  local matches
  local count
  matches=$(search_cmd_matches "$regex")
  count=$(printf "%s\n" "$matches" | sed '/^$/d' | wc -l | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    echo "  MISSING: $label"
    EXIT_CODE=1
  else
    echo "  OK: $label ($count matches)"
  fi
}

check_cmd_pattern "output flag (--output)" '^\$ .*--output([[:space:]]|$)'
check_cmd_pattern "output short alias (-o)" '^\$ .* -o([[:space:]]|$)'
check_cmd_pattern "width flag (--width)" '^\$ .*--width([[:space:]]|$)'
check_cmd_pattern "width short alias (-w)" '^\$ .* -w([[:space:]]|$)'
check_cmd_pattern "plaintext flag (--plaintext)" '^\$ .*--plaintext([[:space:]]|$)'
check_cmd_pattern "plaintext short alias (-p)" '^\$ .* -p([[:space:]]|$)'
check_cmd_pattern "semantic flag (--semantic)" '^\$ .*--semantic([[:space:]]|$)'
check_cmd_pattern "semantic short alias (-s)" '^\$ .* -s([[:space:]]|$)'
check_cmd_pattern "cleanups flag (--cleanups)" '^\$ .*--cleanups([[:space:]]|$)'
check_cmd_pattern "cleanups short alias (-c)" '^\$ .* -c([[:space:]]|$)'
check_cmd_pattern "smartquotes flag (--smartquotes)" '^\$ .*--smartquotes([[:space:]]|$)'
check_cmd_pattern "ellipses flag (--ellipses)" '^\$ .*--ellipses([[:space:]]|$)'
check_cmd_pattern "list spacing flag (--list-spacing)" '^\$ .*--list-spacing([[:space:]]|$)'
check_cmd_pattern "inplace flag (--inplace)" '^\$ .*--inplace([[:space:]]|$)'
check_cmd_pattern "inplace short alias (-i)" '^\$ .* -i([[:space:]]|$)'
check_cmd_pattern "no backup flag (--nobackup)" '^\$ .*--nobackup([[:space:]]|$)'
check_cmd_pattern "auto mode (--auto)" '^\$ .*--auto([[:space:]]|$)'
check_cmd_pattern "extend include (--extend-include)" '^\$ .*--extend-include([[:space:]]|$)'
check_cmd_pattern "exclude replacement (--exclude)" '^\$ .*--exclude([[:space:]]|$)'
check_cmd_pattern "extend exclude (--extend-exclude)" '^\$ .*--extend-exclude([[:space:]]|$)'
check_cmd_pattern "gitignore toggle (--no-respect-gitignore)" '^\$ .*--no-respect-gitignore([[:space:]]|$)'
check_cmd_pattern "force exclude (--force-exclude)" '^\$ .*--force-exclude([[:space:]]|$)'
check_cmd_pattern "list files (--list-files)" '^\$ .*--list-files([[:space:]]|$)'
check_cmd_pattern "max file size (--files-max-size)" '^\$ .*--files-max-size([[:space:]]|$)'
check_cmd_pattern "version flag (--version)" '^\$ .*--version([[:space:]]|$)'
check_cmd_pattern "help flag (--help)" '^\$ .*--help([[:space:]]|$)'
check_cmd_pattern "skill flag (--skill)" '^\$ .*--skill([[:space:]]|$)'
check_cmd_pattern "install skill flag (--install-skill)" '^\$ .*--install-skill([[:space:]]|$)'
check_cmd_pattern "agent base flag (--agent-base)" '^\$ .*--agent-base([[:space:]]|$)'
check_cmd_pattern "docs flag (--docs)" '^\$ .*--docs([[:space:]]|$)'

echo ""
echo "Checking wildcard discipline..."
UNKNOWN_WILDCARDS=$(rg -n '\[\?\?\]|^\?\?\?$' "$TESTS_DIR"/*.tryscript.md 2>/dev/null || true)
if ! command -v rg >/dev/null 2>&1; then
  UNKNOWN_WILDCARDS=$(grep -nE '\[\?\?\]|^\?\?\?$' "$TESTS_DIR"/*.tryscript.md 2>/dev/null || true)
fi
if [ -n "$UNKNOWN_WILDCARDS" ]; then
  echo "ERROR: Found unknown wildcard placeholders ([??] or ???):"
  echo "$UNKNOWN_WILDCARDS"
  EXIT_CODE=1
else
  echo "OK: no unknown wildcard placeholders"
fi

echo ""
FILE_COUNT=$(find "$TESTS_DIR" -name "*.tryscript.md" | wc -l | tr -d ' ')
FIXTURE_COUNT=$(find "$TESTS_DIR/fixtures" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "Tryscript files: $FILE_COUNT"
echo "Fixture files: $FIXTURE_COUNT"

exit "$EXIT_CODE"
