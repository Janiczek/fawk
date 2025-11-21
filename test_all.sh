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
    shift 2
    local input_files=("$@")
    local expected_stdout="tests/${basename}.stdout"
    local expected_stderr="tests/${basename}.stderr"
    local expected_exitcode="tests/${basename}.exitcode"
    local env_file="tests/${basename}.env"
    local check_gawk="false"
    
    # Determine if this is a gawk compatibility test
    if [[ "$script" == *.awk ]]; then
        check_gawk="true"
    fi
    
    TOTAL=$((TOTAL + 1))
    
    # Run the test with fawk, capturing stdout and stderr separately
    local actual_stdout=$(mktemp)
    local actual_stderr=$(mktemp)
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
        
        if [ ${#input_files[@]} -gt 0 ]; then
            ./fawk "$script" "${input_files[@]}"
        else
            ./fawk "$script"
        fi
    ) > "$actual_stdout" 2> "$actual_stderr" || exit_code=$?
    
    # Determine expected exit code (default 0 if file missing)
    local expected_exit=0
    if [ -f "$expected_exitcode" ]; then
        expected_exit=$(cat "$expected_exitcode" | tr -d '[:space:]')
        # Handle empty file as 0
        if [ -z "$expected_exit" ]; then
            expected_exit=0
        fi
    fi
    
    # Check exit code (always tested)
    local test_failed=false
    if [ $exit_code -ne $expected_exit ]; then
        echo -e "${RED}✗ FAILED${NC}: $basename"
        echo "  Exit code mismatch: expected $expected_exit, got $exit_code"
        test_failed=true
    fi
    
    # Check stdout (if expected file exists)
    if [ -f "$expected_stdout" ]; then
        if ! diff -q "$expected_stdout" "$actual_stdout" > /dev/null 2>&1; then
            if [ "$test_failed" = "false" ]; then
                echo -e "${RED}✗ FAILED${NC}: $basename"
            fi
            echo "  Stdout differs from expected:"
            diff -u "$expected_stdout" "$actual_stdout" | head -20
            test_failed=true
        fi
    fi
    
    # Check stderr (always tested, empty if file missing)
    local expected_stderr_file=$(mktemp)
    if [ -f "$expected_stderr" ]; then
        cp "$expected_stderr" "$expected_stderr_file"
    else
        touch "$expected_stderr_file"
    fi
    
    if ! diff -q "$expected_stderr_file" "$actual_stderr" > /dev/null 2>&1; then
        if [ "$test_failed" = "false" ]; then
            echo -e "${RED}✗ FAILED${NC}: $basename"
        fi
        echo "  Stderr differs from expected:"
        diff -u "$expected_stderr_file" "$actual_stderr" | head -20
        test_failed=true
    fi
    rm -f "$expected_stderr_file"
    
    if [ "$test_failed" = "true" ]; then
        FAILED=$((FAILED + 1))
        rm -f "$actual_stdout" "$actual_stderr"
        return
    fi
    
    # Check gawk compatibility if requested (only for tests with expected stdout files)
    if [ "$check_gawk" = "true" ] && [ -f "$expected_stdout" ]; then
        if ! command -v gawk &> /dev/null; then
            echo -e "${YELLOW}⚠ WARNING${NC}: $basename - gawk not found, skipping compatibility check"
            rm -f "$actual_stdout" "$actual_stderr"
            PASSED=$((PASSED + 1))
            return
        fi
        
        # Check if script uses PREC variable (requires gawk -M)
        local gawk_flags=""
        if grep -q "PREC" "$script" 2>/dev/null; then
            gawk_flags="-M"
        fi
        
        local gawk_stdout=$(mktemp)
        local gawk_stderr=$(mktemp)
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
            
            if [ ${#input_files[@]} -gt 0 ]; then
                gawk $gawk_flags -f "$script" "${input_files[@]}"
            else
                gawk $gawk_flags -f "$script"
            fi
        ) > "$gawk_stdout" 2> "$gawk_stderr" || gawk_exit_code=$?
    
        # Compare fawk and gawk stdout outputs
        if ! diff -q "$actual_stdout" "$gawk_stdout" > /dev/null 2>&1; then
            echo -e "${RED}✗ GAWK COMPATIBILITY FAILED${NC}: $basename"
            echo "  FAWK and GAWK stdout outputs differ:"
            diff -u "$actual_stdout" "$gawk_stdout" | head -20
            echo ""
            FAILED=$((FAILED + 1))
            PASSED=$((PASSED - 1))
        fi
        
        rm -f "$gawk_stdout" "$gawk_stderr"
    fi
    
    PASSED=$((PASSED + 1))
    rm -f "$actual_stdout" "$actual_stderr"
}

# Discover and run all tests
for script in tests/*.fawk tests/*.awk; do
    if [ -f "$script" ]; then
        # Extract basename without extension
        basename=$(basename "$script" .fawk)
        basename=$(basename "$basename" .awk)
        
        # Find all matching input files using glob pattern
        # This automatically handles single or multiple input files
        input_files=()
        for input_file in tests/${basename}.input*; do
            if [ -f "$input_file" ]; then
                input_files+=("$input_file")
            fi
        done
        
        run_test "$script" "$basename" "${input_files[@]}"
    fi
done

# Summary of .fawk tests
echo "E2E tests: $PASSED passed, $FAILED failed"

./tests/test_command_line.sh