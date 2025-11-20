# FAWK Examples

This directory contains examples demonstrating FAWK's features.

## Running Examples

```bash
# Run a specific example
./fawk examples/01_functions.fawk

# Run the CSV example (needs data file)
./fawk examples/09_csv.fawk examples/data.csv

# Run all examples
make test
```

## Example Descriptions

1. **01_functions.fawk** - Functions as first-class values
2. **02_arrays.fawk** - Array literals
3. **03_lambda.fawk** - Anonymous functions with multi-statement bodies
4. **04_pipeline.fawk** - Pipeline operator with map/filter
5. **05_nested_arrays.fawk** - Nested arrays
6. **06_associative.fawk** - Associative arrays
7. **07_reduce.fawk** - Pipeline with reduce
8. **08_closure.fawk** - Lexical scope and closures
9. **09_csv.fawk** - Complete CSV processing example with pattern-actions

## Expected Outputs

- **01_functions.fawk**: `42`
- **02_arrays.fawk**: `[1, 2, 3, 4, 5]`
- **03_lambda.fawk**: `42`
- **04_pipeline.fawk**: `[4, 8, 12, 16, 20]`
- **05_nested_arrays.fawk**: Three lines of pairs: `1 2`, `3 4`, `5 6`
- **06_associative.fawk**: `95`
- **07_reduce.fawk**: `20`
- **08_closure.fawk**: `35`
- **09_csv.fawk**: Category averages for electronics, books, and clothing
