# FAWK - Functional AWK

A functional AWK dialect with first-class functions, arrays and lexical scope.

Not all AWK features are supported, but should be enough of them to be dangerous.

```awk
function make_adder(k) {
    return (x) => { return x + k }  # lambdas
}

function make_range(n) {
    for (i = 1; i <= n; i++) {  # locals don't leak!
        arr[length(arr)] = i
    }
    return arr  # returning arrays!
}

END {
    src = make_range(3)
    add5 = make_adder(5)
    result = src |> map(add5)  # pipelines, fns as values, map/filter/reduce
    print(result)  # printing arrays
}

# --> [6, 7, 8]
```

> [!WARNING]  
> I am ~ashamed~ surprised to say the implementation of this interpreter is 100%
> written by a LLM. I've only steered it via the test suite, and it _is_ passing
> it (alongside compatibility with GAWK, where tested).
>
> Unfortunately this means that I am not familiar with the codebase. Do not rely
> on this in production. I'm only planning on using this on Advent of Code myself.

## What's Different

1. [Arrays as First-Class Values](#1-arrays-as-first-class-values) - create, pass, and return arrays
2. [Functions as First-Class Values](#2-functions-as-first-class-values) - pass functions as arguments
3. [Anonymous Functions](#3-anonymous-functions) - arrow syntax `(x) => { x * 2 }`
4. [Functional Pipeline Operator](#4-functional-pipeline-operator) - compose operations with `|>`
5. [Higher-Order Functions](#5-higher-order-functions) - map, filter, and custom combinators
6. [Lexical Scope](#6-lexical-scope) - local-by-default, no action at a distance
7. [Explicit Globals](#7-explicit-globals) - declare globals with `global` keyword
8. [Array Destructuring](#8-array-destructuring) - pluck data from arrays

### 1. Arrays as First-Class Values

Arrays can be created, passed to functions, and returned from functions.

**Regular arrays:**
```awk
numbers = [1, 2, 3, 4, 5]
sum_array(numbers)
```

**Nested arrays:**
```awk
matrix = [[1, 2], [3, 4], [5, 6]]
for (i in matrix) {
    row = matrix[i]
    print row[0], row[1]
}
```

**Associative arrays:**
```awk
scores = ["alice" => 95, "bob" => 87, "carol" => 92]
print scores["alice"]
```


### 2. Functions as First-Class Values

Top-level functions can be used as values:

```awk
function double(x) { return x * 2 }
function apply(func, value) { return func(value) }

BEGIN {
    result = apply(double, 21)  # Returns 42
    print result
}
```

### 3. Anonymous Functions

Create inline functions with arrow syntax:

**Full syntax:**
```awk
add = (a, b) => {
    c = a + b
    return c
}
print add(10, 32)  # Prints 42
```

**Shorthand for single expressions:**
```awk
square = (x) => { x * x }
triple = (x) => { x * 3 }

numbers = [1, 2, 3, 4, 5]
map(square, numbers)  # [1, 4, 9, 16, 25]
```

### 4. Functional Pipeline Operator

Chain operations elegantly with `|>`. The left side becomes the rightmost argument of the function on the right:

```awk
# These are equivalent:
doubled = nums |> filter((n) => { n % 2 == 0 }) |> map((n) => { n * 2 })
doubled = map((n) => { n * 2 }, filter((n) => { n % 2 == 0 }, nums))

# More examples:
result = [1, 2, 3, 4, 5] 
    |> filter((x) => { x % 2 == 0 })  # [2, 4]
    |> map((x) => { x * x })           # [4, 16]
    |> reduce((acc, x) => { acc + x }, 0)  # 20
```

### 5. Higher-Order Functions

Combine arrays and functions for powerful data processing:

```awk
# map, filter, reduce, sum_array are built-in (but you could have written them youself)
# split, match return an array instead of taking one as an "out-parameter"

BEGIN {
    # Works with regular arrays
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    doubled = nums 
        |> filter((n) => { n % 2 == 0 }) 
        |> map((n) => { n * 2 })
    print doubled  # [4, 8, 12, 16, 20]
    
    # Works with associative arrays too
    scores = ["alice" => 95, "bob" => 67, "carol" => 88]
    passing = scores |> filter((s) => { s >= 70 })
    print passing  # [95, 88]
}
```

### 6. Lexical Scope

Variables are local by default. No spooky action at a distance.

```awk
function outer(x) {
    y = x + 10  # Local to outer()
    
    inner = (z) => {
        w = z + 5  # Local to inner()
        return w
    }
    
    return inner(y)
}

BEGIN {
    result = outer(20)  # Returns 35
    # y and w don't exist here
}
```

Arrays and scalars are passed to functions by-value (the function cannot change their contents, it can only return a new array).
On the other hand global values are mutable.

### 7. Explicit Globals

Globals must be declared in the BEGIN block:

```awk
BEGIN {
    global total, count, max_value
}

{
    total = total + $1
    count = count + 1
    if ($1 > max_value) {
        max_value = $1
    }
}

END {
    print "Average:", total / count
    print "Maximum:", max_value
}
```

### 8. Array Destructuring

Arrays can be destructured when receiving function call results or assigning from arrays:

**Simple destructuring:**
```awk
[_, x, y] = match(/-x([0-9]+)-y([0-9]+)$/, $1)
[a, b, c] = "a-b-c" |> split("-")
```

**Nested destructuring:**
```awk
my_nested = [[1, 2], [3, 4]]
[[x, y], [z, w]] = my_nested
```