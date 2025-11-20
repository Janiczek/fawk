#!/usr/bin/env python3
"""
Test runner for FAWK interpreter
Compares actual output against expected output for each test
"""

import subprocess
import sys
from pathlib import Path

# Test definitions: (script, input_file, expected_output_file)
TESTS = [
    ("test1_arrays.fawk", None, "test1_arrays.expected"),
    ("test2_functions.fawk", None, "test2_functions.expected"),
    ("test3_lambda.fawk", None, "test3_lambda.expected"),
    ("test4_pipeline.fawk", None, "test4_pipeline.expected"),
    ("test5_higher_order.fawk", None, "test5_higher_order.expected"),
    ("test6_lexical_scope.fawk", None, "test6_lexical_scope.expected"),
    ("test7_csv.fawk", "sales.csv", "test7_csv.expected"),
]

def run_test(script, input_file, expected_file):
    """Run a single test and compare output"""
    cmd = ["python3", "fawk.py", script]
    if input_file:
        cmd.append(input_file)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        actual_output = result.stdout
        
        # Read expected output
        with open(expected_file, 'r') as f:
            expected_output = f.read()
        
        # Compare
        if actual_output == expected_output:
            return True, None
        else:
            return False, {
                'expected': expected_output,
                'actual': actual_output,
                'returncode': result.returncode,
                'stderr': result.stderr
            }
    
    except subprocess.TimeoutExpired:
        return False, {'error': 'Test timed out'}
    except FileNotFoundError as e:
        return False, {'error': f'File not found: {e}'}
    except Exception as e:
        return False, {'error': f'Error running test: {e}'}

def main():
    print("=" * 70)
    print("FAWK Interpreter Test Suite")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for i, (script, input_file, expected_file) in enumerate(TESTS, 1):
        test_name = script.replace('.fawk', '')
        input_desc = f" (with {input_file})" if input_file else ""
        print(f"Test {i}/{len(TESTS)}: {test_name}{input_desc}")
        print("-" * 70)
        
        success, error_info = run_test(script, input_file, expected_file)
        
        if success:
            print("✓ PASSED")
            passed += 1
        else:
            print("✗ FAILED")
            failed += 1
            
            if error_info:
                if 'error' in error_info:
                    print(f"  Error: {error_info['error']}")
                else:
                    print(f"  Expected output:")
                    print("  " + "\n  ".join(error_info['expected'].split('\n')[:10]))
                    if len(error_info['expected'].split('\n')) > 10:
                        print("  ...")
                    print(f"  Actual output:")
                    print("  " + "\n  ".join(error_info['actual'].split('\n')[:10]))
                    if len(error_info['actual'].split('\n')) > 10:
                        print("  ...")
                    if error_info.get('stderr'):
                        print(f"  Stderr: {error_info['stderr'][:500]}")
        
        print()
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(TESTS)} tests")
    print("=" * 70)
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
