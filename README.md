# FAWK - Functional AWK

A functional AWK dialect with first-class functions and arrays. FAWK keeps AWK's succinct syntax while adding modern functional programming features.

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
map(numbers, square)  # [1, 4, 9, 16, 25]
```

### 4. Higher-Order Functions

Combine arrays and functions for powerful data processing:

```awk
function map(arr, func) {
    result = []
    for (i in arr) {
        result[i] = func(arr[i])
    }
    return result
}

function filter(arr, pred) {
    result = []
    idx = 0
    for (i in arr) {
        if (pred(arr[i])) {
            result[idx] = arr[i]
            idx = idx + 1
        }
    }
    return result
}

BEGIN {
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    evens = filter(nums, (n) => { n % 2 == 0 })
    doubled = map(evens, (n) => { n * 2 })
    print doubled  # [4, 8, 12, 16, 20]
}
```

### 5. Lexical Scope

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

### 6. Explicit Globals

Globals must be declared in the BEGIN block:

```awk
BEGIN {
    global total, count, max_value
    total = 0
    count = 0
    max_value = 0
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
BEGIN {
    global sales, categories
    sales = ["electronics" => [], "books" => [], "clothing" => []]
}

# Parse CSV: category,product,price
NR > 1 {
    category = $1
    price = $3
    sales[category][length(sales[category])] = price
}

END {
    get_sum = (arr) => {
        total = 0
        for (i in arr) { total = total + arr[i] }
        return total
    }
    
    get_avg = (arr) => { get_sum(arr) / length(arr) }
    
    for (cat in sales) {
        avg = get_avg(sales[cat])
        print cat, "average:", avg
    }
}
```

## Design Principles

- **Succinct**: Keep AWK's brevity for text processing
- **Functional**: First-class functions and arrays enable composable code
- **Predictable**: Lexical scope eliminates hidden state
- **Explicit**: Globals must be declared, no implicit behavior
