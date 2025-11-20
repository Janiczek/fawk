# FAWK - Functional AWK

A functional AWK dialect with first-class functions and arrays. FAWK keeps AWK's succinct syntax while adding modern functional programming features.

## What's New

1. [Arrays as First-Class Values](#1-arrays-as-first-class-values) - create, pass, and return arrays
2. [Functions as First-Class Values](#2-functions-as-first-class-values) - pass functions as arguments
3. [Anonymous Functions](#3-anonymous-functions) - arrow syntax `(x) => { x * 2 }`
4. [Functional Pipeline Operator](#4-functional-pipeline-operator) - compose operations with `|>`
5. [Higher-Order Functions](#5-higher-order-functions) - map, filter, and custom combinators
6. [Lexical Scope](#6-lexical-scope) - local-by-default, no action at a distance
7. [Explicit Globals](#7-explicit-globals) - declare globals with `global` keyword

## Key Features

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
function map(func, arr) {
    result = []
    for (i in arr) {
        result[i] = func(arr[i])
    }
    return result
}

function filter(pred, arr) {
    result = []
    # Works with both regular and associative arrays
    for (key in arr) {
        if (pred(arr[key])) {
            result[key] = arr[key]
        }
    }
    return result
}

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
    print passing  # [95, 88] (values that passed the filter)
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

## Complete Example: Processing CSV Data

```awk
function sum(arr) {
    total = 0
    for (i in arr) { total = total + arr[i] }
    return total
}

function avg(arr) {
    return sum(arr) / length(arr)
}

BEGIN {
    global sales
    sales = ["electronics" => [], "books" => [], "clothing" => []]
}

# Parse CSV: category,product,price
NR > 1 {
    category = $1
    price = $3
    sales[category][length(sales[category])] = price
}

END {
    for (cat in sales) {
        average = avg(sales[cat])
        print cat, "average:", average
    }
}
```

