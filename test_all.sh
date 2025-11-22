#!/usr/bin/env bash
# FAWK Test Suite
# Runs all tests and validates output against expected results

set -e

cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine number of parallel jobs (use CPU count, but cap at 8)
if command -v nproc &> /dev/null; then
    MAX_JOBS=$(nproc)
elif [ -f /proc/cpuinfo ]; then
    MAX_JOBS=$(grep -c processor /proc/cpuinfo)
else
    # macOS fallback
    MAX_JOBS=$(sysctl -n hw.ncpu 2>/dev/null || echo 4)
fi
if [ "$MAX_JOBS" -gt 8 ]; then
    MAX_JOBS=8
fi

# Results directory for parallel execution
RESULTS_DIR=$(mktemp -d)
trap "rm -rf $RESULTS_DIR" EXIT

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
    local result_file="$RESULTS_DIR/${basename}.result"
    
    # Determine if this is a gawk compatibility test
    if [[ "$script" == *.awk ]]; then
        check_gawk="true"
    fi
    
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
            ./fawk -f "$script" "${input_files[@]}"
        else
            ./fawk -f "$script"
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
    local output=""
    if [ $exit_code -ne $expected_exit ]; then
        output="${output}${RED}✗ FAILED${NC}: $basename\n"
        output="${output}  Exit code mismatch: expected $expected_exit, got $exit_code\n"
        test_failed=true
    fi
    
    # Check stdout (if expected file exists)
    if [ -f "$expected_stdout" ]; then
        if ! diff -q "$expected_stdout" "$actual_stdout" > /dev/null 2>&1; then
            if [ "$test_failed" = "false" ]; then
                output="${output}${RED}✗ FAILED${NC}: $basename\n"
            fi
            output="${output}  Stdout differs from expected:\n"
            output="${output}$(diff -u "$expected_stdout" "$actual_stdout" | head -20)\n"
            test_failed=true
        fi
    fi
    
    # Check stderr (always tested, empty if file missing)
    # Optimize: avoid temp file copy if expected_stderr doesn't exist
    if [ -f "$expected_stderr" ]; then
        if ! diff -q "$expected_stderr" "$actual_stderr" > /dev/null 2>&1; then
            if [ "$test_failed" = "false" ]; then
                output="${output}${RED}✗ FAILED${NC}: $basename\n"
            fi
            output="${output}  Stderr differs from expected:\n"
            output="${output}$(diff -u "$expected_stderr" "$actual_stderr" | head -20)\n"
            test_failed=true
        fi
    else
        # Check if stderr is non-empty when it should be empty
        if [ -s "$actual_stderr" ]; then
            if [ "$test_failed" = "false" ]; then
                output="${output}${RED}✗ FAILED${NC}: $basename\n"
            fi
            output="${output}  Stderr differs from expected (expected empty):\n"
            output="${output}$(head -20 "$actual_stderr")\n"
            test_failed=true
        fi
    fi
    
    if [ "$test_failed" = "true" ]; then
        echo -e "FAILED" > "$result_file"
        echo -e "$output" >> "$result_file"
        rm -f "$actual_stdout" "$actual_stderr"
        return
    fi
    
    # Check gawk compatibility if requested (only for tests with expected stdout files)
    if [ "$check_gawk" = "true" ] && [ -f "$expected_stdout" ]; then
        if ! command -v gawk &> /dev/null; then
            echo -e "PASSED" > "$result_file"
            echo -e "${YELLOW}⚠ WARNING${NC}: $basename - gawk not found, skipping compatibility check" >> "$result_file"
            rm -f "$actual_stdout" "$actual_stderr"
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
            echo -e "FAILED" > "$result_file"
            echo -e "${RED}✗ GAWK COMPATIBILITY FAILED${NC}: $basename" >> "$result_file"
            echo -e "  FAWK and GAWK stdout outputs differ:" >> "$result_file"
            diff -u "$actual_stdout" "$gawk_stdout" | head -20 >> "$result_file"
            echo "" >> "$result_file"
            rm -f "$gawk_stdout" "$gawk_stderr" "$actual_stdout" "$actual_stderr"
            return
        fi
        
        rm -f "$gawk_stdout" "$gawk_stderr"
    fi
    
    echo -e "PASSED" > "$result_file"
    rm -f "$actual_stdout" "$actual_stderr"
}

# Command-line test runner
run_cmdline_test() {
    local cmdtest_file="$1"
    local basename="$2"
    local expected_stdout="tests/${basename}.stdout"
    local expected_stderr="tests/${basename}.stderr"
    local expected_exitcode="tests/${basename}.exitcode"
    local result_file="$RESULTS_DIR/${basename}.result"
    local test_dir=$(mktemp -d)
    
    # Read the command from .cmdtest file (trim trailing newline)
    local test_cmd=$(cat "$cmdtest_file" | tr -d '\n' | sed 's/[[:space:]]*$//')
    
    # Create test files in this test's directory
    echo "apple" > "$test_dir/file1.txt"
    echo "banana" > "$test_dir/file2.txt"
    echo "cherry" > "$test_dir/file3.txt"
    echo "one:two:three" > "$test_dir/fields.txt"
    echo '{ print $0 }' > "$test_dir/script.fawk"
    echo 'BEGIN { FS = ":" } { print $2 }' > "$test_dir/fields_script.fawk"
    
    # Check if this is a redirect test (command writes to a file) BEFORE placeholder replacement
    local is_redirect_test=false
    local redirect_file=""
    if [[ "$test_cmd" =~ \"REDIRECT\" ]]; then
        is_redirect_test=true
        redirect_file="$test_dir/redirect.txt"
    elif [[ "$test_cmd" =~ \"APPEND\" ]]; then
        is_redirect_test=true
        redirect_file="$test_dir/append.txt"
    elif [[ "$test_cmd" =~ \"PRINTF_REDIRECT\" ]]; then
        is_redirect_test=true
        redirect_file="$test_dir/printf_redirect.txt"
    elif [[ "$test_cmd" =~ \"PRINTF_APPEND\" ]]; then
        is_redirect_test=true
        redirect_file="$test_dir/printf_append.txt"
    fi
    
    # Replace placeholders in command with actual paths
    # Replace longer patterns first to avoid partial matches
    local cmd="${test_cmd//FIELDS_SCRIPT/$test_dir/fields_script.fawk}"
    cmd="${cmd//PRINTF_REDIRECT/$test_dir/printf_redirect.txt}"
    cmd="${cmd//PRINTF_APPEND/$test_dir/printf_append.txt}"
    cmd="${cmd//FILE1/$test_dir/file1.txt}"
    cmd="${cmd//FILE2/$test_dir/file2.txt}"
    cmd="${cmd//FILE3/$test_dir/file3.txt}"
    cmd="${cmd//FIELDS/$test_dir/fields.txt}"
    cmd="${cmd//SCRIPT/$test_dir/script.fawk}"
    cmd="${cmd//REDIRECT/$test_dir/redirect.txt}"
    cmd="${cmd//APPEND/$test_dir/append.txt}"
    
    # Determine expected exit code (default 0 if file missing)
    local expected_exit=0
    if [ -f "$expected_exitcode" ]; then
        expected_exit=$(cat "$expected_exitcode" | tr -d '[:space:]')
        if [ -z "$expected_exit" ]; then
            expected_exit=0
        fi
    fi
    
    # Run the command, capturing stdout and stderr separately
    local actual_stdout=$(mktemp)
    local actual_stderr=$(mktemp)
    local exit_code=0
    
    if [ "$is_redirect_test" = "true" ]; then
        # For redirect tests, run command and read from the output file
        eval "$cmd" > /dev/null 2> "$actual_stderr" || exit_code=$?
        if [ -f "$redirect_file" ]; then
            cat "$redirect_file" > "$actual_stdout"
        fi
    else
        # Normal test - capture stdout and stderr
        eval "$cmd" > "$actual_stdout" 2> "$actual_stderr" || exit_code=$?
    fi
    
    # Check exit code
    local test_failed=false
    local output=""
    if [ $exit_code -ne $expected_exit ]; then
        output="${output}${RED}✗ FAILED${NC}: $basename\n"
        output="${output}  Exit code mismatch: expected $expected_exit, got $exit_code\n"
        test_failed=true
    fi
    
    # Check stdout (if expected file exists)
    if [ -f "$expected_stdout" ]; then
        if ! diff -q "$expected_stdout" "$actual_stdout" > /dev/null 2>&1; then
            if [ "$test_failed" = "false" ]; then
                output="${output}${RED}✗ FAILED${NC}: $basename\n"
            fi
            output="${output}  Stdout differs from expected:\n"
            output="${output}$(diff -u "$expected_stdout" "$actual_stdout" | head -20)\n"
            test_failed=true
        fi
    fi
    
    # Check stderr (always tested, empty if file missing)
    if [ -f "$expected_stderr" ]; then
        if ! diff -q "$expected_stderr" "$actual_stderr" > /dev/null 2>&1; then
            if [ "$test_failed" = "false" ]; then
                output="${output}${RED}✗ FAILED${NC}: $basename\n"
            fi
            output="${output}  Stderr differs from expected:\n"
            output="${output}$(diff -u "$expected_stderr" "$actual_stderr" | head -20)\n"
            test_failed=true
        fi
    else
        # Check if stderr is non-empty when it should be empty
        if [ -s "$actual_stderr" ]; then
            if [ "$test_failed" = "false" ]; then
                output="${output}${RED}✗ FAILED${NC}: $basename\n"
            fi
            output="${output}  Stderr differs from expected (expected empty):\n"
            output="${output}$(head -20 "$actual_stderr")\n"
            test_failed=true
        fi
    fi
    
    if [ "$test_failed" = "true" ]; then
        echo -e "FAILED" > "$result_file"
        echo -e "$output" >> "$result_file"
    else
        echo -e "PASSED" > "$result_file"
    fi
    
    rm -f "$actual_stdout" "$actual_stderr"
    rm -rf "$test_dir"
}

# Export functions and variables for parallel execution
export -f run_test run_cmdline_test
export RED GREEN YELLOW NC RESULTS_DIR

# Discover all file-based tests
TEST_LIST=()
for script in tests/*.fawk tests/*.awk; do
    if [ -f "$script" ]; then
        # Extract basename without extension
        basename=$(basename "$script" .fawk)
        basename=$(basename "$basename" .awk)
        
        # Find all matching input files using glob pattern
        input_files=()
        for input_file in tests/${basename}.input*; do
            if [ -f "$input_file" ]; then
                input_files+=("$input_file")
            fi
        done
        
        TEST_LIST+=("file|$script|$basename|${input_files[*]}")
    fi
done

# Discover all command-line tests
for cmdtest_file in tests/*.cmdtest; do
    if [ -f "$cmdtest_file" ]; then
        # Extract basename without extension
        basename=$(basename "$cmdtest_file" .cmdtest)
        TEST_LIST+=("cmdline|$cmdtest_file|$basename")
    fi
done

# Run tests in parallel using background jobs
TOTAL=${#TEST_LIST[@]}
PASSED=0
FAILED=0
RUNNING=0

for test_spec in "${TEST_LIST[@]}"; do
    # Wait for a job slot if we're at max capacity
    while [ $RUNNING -ge $MAX_JOBS ]; do
        wait -n
        RUNNING=$((RUNNING - 1))
    done
    
    # Parse test specification
    IFS='|' read -r test_type rest <<< "$test_spec"
    
    if [ "$test_type" = "file" ]; then
        IFS='|' read -r script basename input_files_str <<< "$rest"
        IFS=' ' read -r -a input_files <<< "$input_files_str"
        run_test "$script" "$basename" "${input_files[@]}" &
    elif [ "$test_type" = "cmdline" ]; then
        IFS='|' read -r cmdtest_file basename <<< "$rest"
        run_cmdline_test "$cmdtest_file" "$basename" &
    fi
    
    RUNNING=$((RUNNING + 1))
done

# Wait for all remaining jobs
while [ $RUNNING -gt 0 ]; do
    wait -n
    RUNNING=$((RUNNING - 1))
done

# Collect and display results
E2E_PASSED=0
E2E_FAILED=0
CMDLINE_PASSED=0
CMDLINE_FAILED=0

for result_file in "$RESULTS_DIR"/*.result; do
    if [ -f "$result_file" ]; then
        status=$(head -1 "$result_file")
        basename=$(basename "$result_file" .result)
        
        if [ "$status" = "PASSED" ]; then
            if [[ "$basename" =~ ^cmdline_ ]]; then
                CMDLINE_PASSED=$((CMDLINE_PASSED + 1))
            else
                E2E_PASSED=$((E2E_PASSED + 1))
            fi
        else
            if [[ "$basename" =~ ^cmdline_ ]]; then
                CMDLINE_FAILED=$((CMDLINE_FAILED + 1))
            else
                E2E_FAILED=$((E2E_FAILED + 1))
            fi
            # Display failure output
            tail -n +2 "$result_file"
        fi
    fi
done

# Summary
echo "E2E tests:          $E2E_PASSED passed, $E2E_FAILED failed"
echo "Command-line tests: $CMDLINE_PASSED passed, $CMDLINE_FAILED failed"

if [ $E2E_FAILED -eq 0 ] && [ $CMDLINE_FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
