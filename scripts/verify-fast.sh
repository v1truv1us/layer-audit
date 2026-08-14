#!/bin/bash
# verify-fast.sh — run only the tests affected by current changes.
# The verifier is the bottleneck of every loop; this makes it cheap enough
# to run every iteration. Falls back to the full suite when mapping fails.
#
# Usage: verify-fast.sh [repo-dir] [base-ref]
# Exit 0 = affected tests green. Exit 1 = failures (or fallback suite failed).

set -uo pipefail

REPO="${1:-.}"
BASE="${2:-}"
cd "$REPO" || exit 1

if [ -z "$BASE" ]; then
  BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main 2>/dev/null || echo "HEAD~1")
fi

CHANGED=$( { git diff --name-only "$BASE" -- 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } | sort -u )

if [ -z "$CHANGED" ]; then
  echo "verify-fast: no changes vs $BASE — nothing to verify"
  exit 0
fi

map_tests() {
  local tests=""
  for f in $CHANGED; do
    case "$f" in
      *.test.*|*.spec.*|test_*.py|*_test.go|*_test.rs|tests/*) tests="$tests $f" ;;
      *.ts|*.tsx|*.js|*.jsx)
        base="${f%.*}"; dir=$(dirname "$f"); name=$(basename "$base")
        for cand in "${base}.test.ts" "${base}.test.tsx" "${base}.test.js" "${base}.spec.ts" \
                    "${dir}/__tests__/${name}.test.ts" "test/${name}.test.ts" "tests/${name}.test.ts"; do
          [ -f "$cand" ] && tests="$tests $cand"
        done ;;
      *.py)
        base="${f%.*}"; name=$(basename "$base")
        for cand in "test_${base##*/}.py" "tests/test_${name}.py" "$(dirname "$f")/test_${name}.py"; do
          [ -f "$cand" ] && tests="$tests $cand"
        done ;;
      *.go)
        pkg=$(dirname "$f")
        [ -n "$(ls "$pkg"/*_test.go 2>/dev/null)" ] && tests="$tests ./$pkg" ;;
    esac
  done
  echo "$tests" | tr ' ' '\n' | sort -u | tr '\n' ' '
}

TESTS=$(map_tests)

run_full() {
  echo "verify-fast: falling back to full suite"
  if [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then bun test
  elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then python3 -m pytest -x -q
  elif [ -f "go.mod" ]; then go test ./...
  elif [ -f "package.json" ]; then npm test --silent
  elif [ -f "Cargo.toml" ]; then cargo test -q
  else echo "verify-fast: no known test framework"; exit 1
  fi
}

if [ -z "${TESTS// /}" ]; then
  run_full
  exit $?
fi

echo "verify-fast: running affected tests:$TESTS"
if [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then bun test $TESTS
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then python3 -m pytest -x -q $TESTS
elif [ -f "go.mod" ]; then go test $TESTS
elif [ -f "package.json" ]; then npx vitest run $TESTS 2>/dev/null || npx jest $TESTS
else run_full
fi
