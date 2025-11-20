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
    local expected="tests/${basename}.expected"
    local env_file="tests/${basename}.env"
    local check_gawk="false"
    
    # Determine if this is a gawk compatibility test
    if [[ "$script" == *.awk ]]; then
        check_gawk="true"
    fi
    
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
        
        if [ ${#input_files[@]} -gt 0 ]; then
            ./fawk "$script" "${input_files[@]}"
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
        
        # Check gawk compatibility if requested (only for tests with expected files)
        if [ "$check_gawk" = "true" ]; then
            if ! command -v gawk &> /dev/null; then
                echo -e "${YELLOW}⚠ WARNING${NC}: $basename - gawk not found, skipping compatibility check"
                rm -f "$actual_output"
                return
            fi
            
            # Check if script uses PREC variable (requires gawk -M)
            local gawk_flags=""
            if grep -q "PREC" "$script" 2>/dev/null; then
                gawk_flags="-M"
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
                
                if [ ${#input_files[@]} -gt 0 ]; then
                    gawk $gawk_flags -f "$script" "${input_files[@]}"
                else
                    gawk $gawk_flags -f "$script"
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
    
    rm -f "$actual_output"
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