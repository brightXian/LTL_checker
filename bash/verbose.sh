#!/bin/bash
EXAMPLES_DIR=${1:-./examples}
OUTPUT_DIR=${2:-./output}
mkdir -p "$OUTPUT_DIR"

for folder in "$EXAMPLES_DIR"/*/; do
    [ -d "$folder" ] || continue
    python ./src/run.py "$folder" --verbose > "$OUTPUT_DIR/$(basename "$folder").txt"
done

echo "Output saved to $OUTPUT_DIR/"
