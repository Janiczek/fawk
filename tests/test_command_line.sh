#!/bin/bash
# Test script for command-line argument handling
# Tests -f flag, inline scripts, and multiple input files

set -e

cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

test_case() {
    local description="$1"
    local expected="$2"
    shift 2
    
    # Run the command
    local actual
    actual=$("$@" 2>&1)
    
    if [ "$actual" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} $description"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} $description"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        FAILED=$((FAILED + 1))
    fi
}

# Create test files
echo "apple" > /tmp/fawk_test_file1.txt
echo "banana" > /tmp/fawk_test_file2.txt
echo "cherry" > /tmp/fawk_test_file3.txt

echo "one:two:three" > /tmp/fawk_test_fields.txt

# Test 1: Inline script with input file
test_case "Inline script with single input file" \
    "apple" \
    ./fawk '{ print $0 }' /tmp/fawk_test_file1.txt

# Test 2: -f flag with input file
echo '{ print $0 }' > /tmp/fawk_test_script.fawk
test_case "-f flag with single input file" \
    "apple" \
    ./fawk -f /tmp/fawk_test_script.fawk /tmp/fawk_test_file1.txt

# Test 3: Multiple input files (inline script)
expected_multi="apple
banana
cherry"
test_case "Inline script with multiple input files" \
    "$expected_multi" \
    ./fawk '{ print $0 }' /tmp/fawk_test_file1.txt /tmp/fawk_test_file2.txt /tmp/fawk_test_file3.txt

# Test 4: Multiple input files (-f flag)
test_case "-f flag with multiple input files" \
    "$expected_multi" \
    ./fawk -f /tmp/fawk_test_script.fawk /tmp/fawk_test_file1.txt /tmp/fawk_test_file2.txt /tmp/fawk_test_file3.txt

# Test 5: BEGIN block with no input
test_case "BEGIN block without input file" \
    "Hello, World!" \
    ./fawk 'BEGIN { print "Hello, World!" }'

# Test 6: Field splitting with inline script
echo 'BEGIN { FS = ":" } { print $2 }' > /tmp/fawk_test_fields_script.fawk
test_case "Field splitting with -f flag" \
    "two" \
    ./fawk -f /tmp/fawk_test_fields_script.fawk /tmp/fawk_test_fields.txt

# Test 7: Inline script with field splitting
test_case "Inline script with field splitting" \
    "two" \
    ./fawk 'BEGIN { FS = ":" } { print $2 }' /tmp/fawk_test_fields.txt

# Test 8: NR counting with multiple files
test_case "NR increments across multiple files" \
    "3" \
    ./fawk 'END { print NR }' /tmp/fawk_test_file1.txt /tmp/fawk_test_file2.txt /tmp/fawk_test_file3.txt

# Test 9: Piping input from another command
test_case "Piping input from cat" \
    "apple" \
    bash -c "cat /tmp/fawk_test_file1.txt | ./fawk '{ print \$1 }'"

# Test 10: Piping with field splitting
test_case "Piping with field splitting" \
    "two" \
    bash -c "echo 'one:two:three' | ./fawk 'BEGIN { FS = \":\" } { print \$2 }'"

# Clean up
rm -f /tmp/fawk_test_file1.txt /tmp/fawk_test_file2.txt /tmp/fawk_test_file3.txt
rm -f /tmp/fawk_test_fields.txt /tmp/fawk_test_script.fawk /tmp/fawk_test_fields_script.fawk

# Summary
echo ""
echo "Command-line tests: $PASSED passed, $FAILED failed"

if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi

