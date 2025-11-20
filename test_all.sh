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

run_test() {
    local script="$1"
    local basename="$2"
    local input_file="$3"
    local expected="$4"
    local env_file="$5"
    local check_gawk="$6"
    
    TOTAL=$((TOTAL + 1))
    
    # Run the test with fawk
    local actual_output=$(mktemp)
    local exit_code=0
    
    # Run in a subshell to isolate environment variables
    (
        # Load environment variables if .env file exists
        if [ -n "$env_file" ] && [ -f "$env_file" ]; then
            while IFS='=' read -r key value || [ -n "$key" ]; do
                # Skip empty lines and comments
                [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
                export "$key=$value"
            done < "$env_file"
        fi
        
        if [ -f "$input_file" ]; then
            ./fawk "$script" "$input_file"
        else
            ./fawk "$script"
        fi
    ) > "$actual_output" 2>&1 || exit_code=$?
    
    # Check results
    if [ -f "$expected" ]; then
        # Expected file exists, compare output
        if diff -q "$expected" "$actual_output" > /dev/null 2>&1; then
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ FAILED${NC}: $basename"
            echo "  Expected output differs from actual output:"
            diff -u "$expected" "$actual_output" | head -20
            echo ""
            FAILED=$((FAILED + 1))
            rm -f "$actual_output"
            return
        fi
    else
        # No expected file, just check exit code
        if [ $exit_code -eq 0 ]; then
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ FAILED${NC}: $basename"
            echo "  Script exited with code $exit_code"
            echo "  Output:"
            cat "$actual_output" | head -20
            echo ""
            FAILED=$((FAILED + 1))
            rm -f "$actual_output"
            return
        fi
    fi
    
    # Check gawk compatibility if requested
    if [ "$check_gawk" = "true" ]; then
        if ! command -v gawk &> /dev/null; then
            echo -e "${YELLOW}⚠ WARNING${NC}: $basename - gawk not found, skipping compatibility check"
            rm -f "$actual_output"
            return
        fi
        
        local gawk_output=$(mktemp)
        local gawk_exit_code=0
        
        # Run with gawk
        (
            # Load environment variables if .env file exists
            if [ -n "$env_file" ] && [ -f "$env_file" ]; then
                while IFS='=' read -r key value || [ -n "$key" ]; do
                    # Skip empty lines and comments
                    [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
                    export "$key=$value"
                done < "$env_file"
            fi
            
            if [ -f "$input_file" ]; then
                gawk -f "$script" "$input_file"
            else
                gawk -f "$script"
            fi
        ) > "$gawk_output" 2>&1 || gawk_exit_code=$?
        
        # Compare fawk and gawk outputs
        if ! diff -q "$actual_output" "$gawk_output" > /dev/null 2>&1; then
            echo -e "${RED}✗ GAWK COMPATIBILITY FAILED${NC}: $basename"
            echo "  FAWK and GAWK outputs differ:"
            diff -u "$actual_output" "$gawk_output" | head -20
            echo ""
            FAILED=$((FAILED + 1))
            PASSED=$((PASSED - 1))
        fi
        
        rm -f "$gawk_output"
    fi
    
    rm -f "$actual_output"
}

# Discover and run all tests
for script in tests/*.fawk; do
    if [ -f "$script" ]; then
        # Extract basename without extension
        basename=$(basename "$script" .fawk)
        
        # Check for corresponding input, expected, and env files
        input_file="tests/${basename}.input"
        expected_file="tests/${basename}.expected"
        env_file="tests/${basename}.env"
        
        run_test "$script" "$basename" "$input_file" "$expected_file" "$env_file" "false"
    fi
done

for script in tests/*.awk; do
    if [ -f "$script" ]; then
        # Extract basename without extension
        basename=$(basename "$script" .awk)
        
        # Check for corresponding input, expected, and env files
        input_file="tests/${basename}.input"
        expected_file="tests/${basename}.expected"
        env_file="tests/${basename}.env"
        
        run_test "$script" "$basename" "$input_file" "$expected_file" "$env_file" "true"
    fi
done

# Summary of .fawk tests
echo "E2E tests: $PASSED passed, $FAILED failed"

./tests/test_command_line.sh