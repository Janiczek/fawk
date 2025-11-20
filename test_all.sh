#!/bin/bash
# FAWK Test Suite
# Runs all tests and validates output against expected results

set -e

cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
TOTAL=0

echo "======================================================================"
echo "FAWK Interpreter Test Suite"
echo "======================================================================"
echo ""

run_test() {
    local test_name="$1"
    local script="$2"
    local input_file="$3"
    local expected="$4"
    
    TOTAL=$((TOTAL + 1))
    
    local input_desc=""
    if [ -n "$input_file" ]; then
        input_desc=" (with $input_file)"
    fi
    
    echo "Test $TOTAL: $test_name$input_desc"
    echo "----------------------------------------------------------------------"
    
    # Run the test
    local actual_output=$(mktemp)
    if [ -n "$input_file" ]; then
        python3 fawk.py "$script" "$input_file" > "$actual_output" 2>&1
    else
        python3 fawk.py "$script" > "$actual_output" 2>&1
    fi
    
    # Compare output
    if diff -q "$expected" "$actual_output" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Expected output differs from actual output:"
        diff -u "$expected" "$actual_output" | head -20
        FAILED=$((FAILED + 1))
    fi
    
    rm -f "$actual_output"
    echo ""
}

# Run all tests
run_test "Arrays as First-Class Values" "test1_arrays.fawk" "" "test1_arrays.expected"
run_test "Functions as First-Class Values" "test2_functions.fawk" "" "test2_functions.expected"
run_test "Anonymous Functions" "test3_lambda.fawk" "" "test3_lambda.expected"
run_test "Functional Pipeline Operator" "test4_pipeline.fawk" "" "test4_pipeline.expected"
run_test "Higher-Order Functions" "test5_higher_order.fawk" "" "test5_higher_order.expected"
run_test "Lexical Scope" "test6_lexical_scope.fawk" "" "test6_lexical_scope.expected"
run_test "CSV Processing" "test7_csv.fawk" "sales.csv" "test7_csv.expected"

# Summary
echo "======================================================================"
echo "Results: $PASSED passed, $FAILED failed out of $TOTAL tests"
echo "======================================================================"

if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
