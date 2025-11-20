# FAWK Testing

This directory contains a comprehensive test suite for the FAWK interpreter.

## Running Tests

### Quick Start

```bash
./test_all.sh
```

Or directly:

```bash
python3 run_tests.py
```

### Individual Tests

```bash
# Run individual test
python3 fawk.py test1_arrays.fawk

# Run CSV test with input
python3 fawk.py test7_csv.fawk sales.csv
```

## Test Files

### Test Scripts

1. **test1_arrays.fawk** - Arrays as first-class values
   - Regular arrays
   - Nested arrays
   - Associative arrays
   - Returning arrays from functions

2. **test2_functions.fawk** - Functions as first-class values
   - Passing functions as arguments
   - Higher-order functions

3. **test3_lambda.fawk** - Anonymous functions (lambdas)
   - Arrow syntax
   - Implicit returns for single expressions

4. **test4_pipeline.fawk** - Pipeline operator
   - Chaining operations with |>
   - Multi-line pipelines

5. **test5_higher_order.fawk** - Higher-order functions
   - map, filter, reduce
   - Works with regular and associative arrays

6. **test6_lexical_scope.fawk** - Lexical scoping
   - Closures
   - Global keyword
   - Variable isolation between scopes

7. **test7_csv.fawk** - CSV processing
   - Reading CSV input
   - Field splitting
   - Aggregation and calculations

### Expected Output Files

Each test has a corresponding `.expected` file containing the expected output:

- `test1_arrays.expected`
- `test2_functions.expected`
- `test3_lambda.expected`
- `test4_pipeline.expected`
- `test5_higher_order.expected`
- `test6_lexical_scope.expected`
- `test7_csv.expected`

### Input Files

- **sales.csv** - Sample CSV data for test7_csv.fawk
  - Contains sales data by category (electronics, books, clothing)
  - Format: category,product,price

## Test Runner

The `run_tests.py` script:
- Runs each test with appropriate inputs
- Captures actual output
- Compares against expected output
- Reports pass/fail for each test
- Provides detailed diff output on failure

## Adding New Tests

1. Create your `.fawk` script (e.g., `test8_newfeature.fawk`)
2. Run it and capture output: `python3 fawk.py test8_newfeature.fawk > test8_newfeature.expected`
3. Add entry to `TESTS` list in `run_tests.py`:
   ```python
   ("test8_newfeature.fawk", None, "test8_newfeature.expected"),
   ```
4. Run test suite to verify: `python3 run_tests.py`

## Test Results

All 7 tests currently pass:
- ✓ test1_arrays
- ✓ test2_functions
- ✓ test3_lambda
- ✓ test4_pipeline
- ✓ test5_higher_order
- ✓ test6_lexical_scope
- ✓ test7_csv
