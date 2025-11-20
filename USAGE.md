# FAWK Usage Guide

## Building

```bash
cargo build --release
```

## Running

```bash
# Run a FAWK script
./target/release/fawk script.fawk

# Run with input from a file
./target/release/fawk script.fawk input.txt

# Run with input from stdin
echo "data" | ./target/release/fawk script.fawk
```

## Examples

### Example 1: First-Class Functions

```bash
cargo run examples/example1_first_class_functions.fawk
# Output: 42
```

### Example 2: Lambda Functions

```bash
cargo run examples/example2_lambda.fawk
# Output: 42
```

### Example 3: Pipeline with Higher-Order Functions

```bash
cargo run examples/example3_pipeline.fawk
# Output: 20
```

### Example 4: AWK Features (globals, fields, pattern-action)

```bash
cargo run examples/example4_awk_features.fawk examples/data.txt
# Output:
# Total: 150
# Count: 5
# Average: 30
```

## Implemented Features

✅ Arrays as first-class values (regular, nested, associative)
✅ Functions as first-class values
✅ Anonymous functions with arrow syntax `(x) => { ... }`
✅ Pipeline operator `|>`
✅ Higher-order functions: `map`, `filter`, `reduce`
✅ Lexical scope (local by default)
✅ Explicit globals with `global` keyword
✅ AWK features: BEGIN/END blocks, pattern-action rules, field variables ($1, $2, etc.), NR
✅ For loops with `for (var in array)`
✅ Implicit return of last expression in functions
✅ Print statement
✅ Built-in `length` function
