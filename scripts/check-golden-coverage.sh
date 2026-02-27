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
check_pattern() {
  local label="$1"
  local pattern="$2"
  local matches
  local count
  matches=$(grep -R -- "$pattern" "$TESTS_DIR" 2>/dev/null || true)
  count=$(printf "%s" "$matches" | wc -l | tr -d ' ')
  if [ "$count" -eq 0 ]; then
    echo "  MISSING: $label ($pattern)"
    EXIT_CODE=1
  else
    echo "  OK: $label ($count matches)"
  fi
}

check_pattern "auto mode" "--auto"
check_pattern "list files" "--list-files"
check_pattern "width control" "--width"
check_pattern "plaintext mode" "--plaintext"
check_pattern "semantic mode" "--semantic"
check_pattern "cleanups mode" "--cleanups"
check_pattern "smartquotes mode" "--smartquotes"
check_pattern "ellipses mode" "--ellipses"
check_pattern "list spacing mode" "--list-spacing"
check_pattern "inplace mode" "--inplace"
check_pattern "no backup mode" "--nobackup"
check_pattern "docs mode" "--docs"
check_pattern "skill mode" "--skill"

OUTPUT_MATCHES=$(grep -R -E -- '--output|-o ' "$TESTS_DIR" 2>/dev/null || true)
OUTPUT_COUNT=$(printf "%s" "$OUTPUT_MATCHES" | wc -l | tr -d ' ')
if [ "$OUTPUT_COUNT" -eq 0 ]; then
  echo "  MISSING: output flag (--output or -o)"
  EXIT_CODE=1
else
  echo "  OK: output flag ($OUTPUT_COUNT matches)"
fi

echo ""
FILE_COUNT=$(find "$TESTS_DIR" -name "*.tryscript.md" | wc -l | tr -d ' ')
FIXTURE_COUNT=$(find "$TESTS_DIR/fixtures" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "Tryscript files: $FILE_COUNT"
echo "Fixture files: $FIXTURE_COUNT"

exit "$EXIT_CODE"
