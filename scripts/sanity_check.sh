#!/bin/bash
# sanity_check.sh - Judge helper script
# Runs make sanity and validates the output format

set -e

echo "=== Running Sanity Check ==="
echo ""

# Run make sanity
echo "Step 1: Running 'make sanity'..."
make sanity
echo ""

# Validate output file exists
echo "Step 2: Checking artifacts/sanity_output.json exists..."
if [ -f "backend/artifacts/sanity_output.json" ]; then
    echo "  PASS: artifacts/sanity_output.json found"
else
    echo "  FAIL: artifacts/sanity_output.json not found"
    exit 1
fi

# Validate JSON format
echo ""
echo "Step 3: Validating JSON format..."
python3 scripts/verify_output.py
echo ""

# Check memory files
echo "Step 4: Checking memory files..."
if [ -f "backend/USER_MEMORY.md" ]; then
    echo "  PASS: USER_MEMORY.md exists"
else
    echo "  WARN: USER_MEMORY.md not found (will be created on first chat)"
fi

if [ -f "backend/COMPANY_MEMORY.md" ]; then
    echo "  PASS: COMPANY_MEMORY.md exists"
else
    echo "  WARN: COMPANY_MEMORY.md not found (will be created on first chat)"
fi

echo ""
echo "=== Sanity Check Complete ==="
