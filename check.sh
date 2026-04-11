#!/bin/bash
EXAMPLES_DIR=${1:-./examples}
PASS=0; FAIL=0
TMP=$(mktemp)
trap "rm -f '$TMP'" EXIT

for folder in "$EXAMPLES_DIR"/*/; do
    [ ! -f "$folder/TS.txt" ] || [ ! -f "$folder/benchmark.txt" ] && continue
    python ./src/run.py "$folder" > "$TMP"
    [ ! -f "$folder/result.txt" ] && echo "[$folder] (no result.txt)" && cat "$TMP" && continue
    if diff -q "$TMP" <(tr -d '\r' < "$folder/result.txt") > /dev/null 2>&1; then
        echo "[$folder] PASS"; PASS=$((PASS+1))
    else
        echo "[$folder] FAIL"
        echo "  Got:      $(tr '\n' ' ' < "$TMP")"
        echo "  Expected: $(tr -d '\r' < "$folder/result.txt" | tr '\n' ' ')"
        FAIL=$((FAIL+1))
    fi
done

echo "Results: $PASS passed, $FAIL failed"
