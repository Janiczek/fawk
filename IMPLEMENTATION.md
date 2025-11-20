# FAWK Implementation

This is a Haskell implementation of the FAWK (Functional AWK) language as specified in README.md.

## Features Implemented

### 1. Core Language Features
- ✅ **Arrays as First-Class Values** - Create, pass, and return arrays
- ✅ **Functions as First-Class Values** - Pass functions as arguments
- ✅ **Anonymous Functions** - Arrow syntax `(x) => { x * 2 }`
- ✅ **Functional Pipeline Operator** - Compose operations with `|>`
- ✅ **Higher-Order Functions** - Built-in map, filter, reduce
- ✅ **Lexical Scope** - Local-by-default variables
- ✅ **Explicit Globals** - Declare globals with `global` keyword

### 2. AWK Compatibility
- ✅ **BEGIN/END blocks** - Execute code before/after processing input
- ✅ **Pattern-action blocks** - Process input lines with patterns
- ✅ **Field variables** - `$1`, `$2`, etc. for accessing fields
- ✅ **Built-in variables** - `NR` (line number)
- ✅ **Implicit numeric conversion** - AWK-style string-to-number coercion

### 3. Data Types
- Integers
- Floating-point numbers
- Strings
- Arrays (both indexed and associative)
- Functions
- Null

## Architecture

### Module Structure
- **AST.hs** - Abstract Syntax Tree definitions
- **Parser.hs** - Megaparsec-based parser for FAWK syntax
- **Eval.hs** - Interpreter with lexical scoping and first-class functions
- **Main.hs** - Main program and AWK-style execution model

### Key Implementation Details

#### Return Statement Handling
Functions use a `StmtResult` type to handle early returns without using exceptions for control flow, avoiding state rollback issues.

#### Pipeline Operator
The `|>` operator specially handles function calls on the right side, appending the left value as the last argument.

#### Lexical Scoping
Variables are local by default. The evaluator maintains a stack of local environments, with globals declared explicitly.

#### Type Coercion
Like AWK, FAWK automatically converts between strings and numbers in numeric contexts, treating null as 0.

## Building

```bash
./build.sh
```

Or manually:
```bash
cabal build
```

## Running

Execute a FAWK script:
```bash
./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk script.fawk [input.txt]
```

Or use inline scripts:
```bash
./dist-newstyle/build/x86_64-linux/ghc-9.4.7/fawk-0.1.0.0/x/fawk/build/fawk/fawk -e 'BEGIN { print 42 }'
```

## Test Files

- **test1.fawk** - First-class functions example
- **test2.fawk** - Anonymous functions with built-in map
- **test3.fawk** - Pipeline operator with user-defined map/filter
- **test_scope.fawk** - Lexical scoping with closures
- **test_reduce.fawk** - Reduce with pipeline composition
- **test_globals.fawk** - Global variables with AWK-style input processing

## Limitations

The following features from standard AWK are not yet implemented:
- Regular expressions
- More built-in functions (split, substr, etc.)
- Multiple input files with FILENAME variable
- printf formatting
- Associative array iteration order guarantees
