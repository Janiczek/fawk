# FAWK Implementation

This is a C implementation of the FAWK language, supporting all features described in the README.

## Architecture

The implementation consists of four main components:

### 1. Lexer (Tokenization)
- Converts source code into tokens
- Handles keywords, operators, literals, identifiers
- Supports single and multi-character operators (e.g., `=>`, `|>`, `==`)
- Skips comments (lines starting with `#`)

### 2. Parser (AST Construction)
- Builds an Abstract Syntax Tree from tokens
- Recursive descent parser with proper operator precedence
- Handles:
  - Function definitions
  - Lambda expressions with arrow syntax
  - Array literals (both regular and associative)
  - Pattern-action blocks (BEGIN, END, and general patterns)
  - Control flow (if, for-in, while)
  - Pipeline operator (`|>`)

### 3. Runtime (Value System)
- Dynamic typing with support for:
  - Numbers (double precision)
  - Strings
  - Arrays (hash table based, supporting both numeric and string keys)
  - Functions (including closures)
  - Built-in functions
- Environment management for lexical scoping
- Proper closure support with captured environments

### 4. Evaluator (Execution)
- Tree-walking interpreter
- Lexical scoping with local-by-default variables
- Support for global variables (via `global` keyword)
- Pattern matching for input line processing
- Special variables: `NR` (line number), `$0`, `$1`, etc. (fields)

## Built-in Functions

- `print(...)` - Print values
- `length(arr)` - Get array/string length
- `map(func, arr)` - Map function over array
- `filter(pred, arr)` - Filter array by predicate
- `reduce(func, initial, arr)` - Reduce array to single value
- `sum(arr)` - Sum array elements
- `avg(arr)` - Average of array elements

## Implementation Details

### Arrays
- Implemented as hash tables with separate chaining
- Support both numeric indices (regular arrays) and string keys (associative arrays)
- Printing logic detects array type and formats output accordingly

### Functions and Closures
- Functions are first-class values
- Lambda expressions capture their defining environment (closure)
- Function calls create new local environments

### Pipeline Operator
- Transformed during parsing
- `x |> f(a, b)` becomes `f(a, b, x)`
- `x |> f` becomes `f(x)`

### Pattern-Action Blocks
- BEGIN and END blocks executed before/after input processing
- General patterns evaluated for each input line
- Only executes action if pattern evaluates to true

## Files

- `fawk.c` - Main implementation (lexer, parser, evaluator)
- `Makefile` - Build configuration
- `examples/` - Example FAWK programs demonstrating features
- `README.md` - Language documentation
- `IMPLEMENTATION.md` - This file

## Limitations

- No regex support (yet)
- No string interpolation
- Pipeline operator must be on same line as operands
- Limited error messages (no line numbers in errors)
- No optimization (direct AST interpretation)

## Future Enhancements

Potential improvements:
- Better error messages with source locations
- Regex pattern matching
- More built-in functions (split, substr, etc.)
- Multi-line pipeline support
- Bytecode compilation for better performance
- Garbage collection for memory management
