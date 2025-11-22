# Test: Ternary operator (condition ? true_expr : false_expr)

BEGIN {
    print "Test: Ternary operator"
    print "--------------------------------------"
    
    # Basic ternary with numbers
    x = 5
    result = x > 3 ? 10 : 20
    print "x =", x, ", x > 3 ? 10 : 20 =", result
    
    y = 2
    result = y > 3 ? 10 : 20
    print "y =", y, ", y > 3 ? 10 : 20 =", result
    print ""
    
    # Ternary with strings
    name = "Alice"
    greeting = name == "Alice" ? "Hello Alice" : "Hello stranger"
    print "name =", name, ", greeting =", greeting
    
    name = "Bob"
    greeting = name == "Alice" ? "Hello Alice" : "Hello stranger"
    print "name =", name, ", greeting =", greeting
    print ""
    
    # Ternary with boolean values
    flag = 1
    status = flag ? "enabled" : "disabled"
    print "flag =", flag, ", status =", status
    
    flag = 0
    status = flag ? "enabled" : "disabled"
    print "flag =", flag, ", status =", status
    print ""
    
    # Ternary in expressions
    a = 10
    b = 20
    max_val = a > b ? a : b
    print "a =", a, ", b =", b, ", max =", max_val
    
    a = 30
    b = 20
    max_val = a > b ? a : b
    print "a =", a, ", b =", b, ", max =", max_val
    print ""
    
    # Nested ternary operators (right-associative)
    score = 85
    grade = score >= 90 ? "A" : score >= 80 ? "B" : score >= 70 ? "C" : "F"
    print "score =", score, ", grade =", grade
    
    score = 95
    grade = score >= 90 ? "A" : score >= 80 ? "B" : score >= 70 ? "C" : "F"
    print "score =", score, ", grade =", grade
    
    score = 75
    grade = score >= 90 ? "A" : score >= 80 ? "B" : score >= 70 ? "C" : "F"
    print "score =", score, ", grade =", grade
    
    score = 65
    grade = score >= 90 ? "A" : score >= 80 ? "B" : score >= 70 ? "C" : "F"
    print "score =", score, ", grade =", grade
    print ""
    
    # More complex nested ternary
    x = 5
    y = 10
    z = 15
    result = x > y ? "x is largest" : y > z ? "y is largest" : "z is largest"
    print "x =", x, ", y =", y, ", z =", z, ", result =", result
    
    x = 20
    y = 10
    z = 15
    result = x > y ? "x is largest" : y > z ? "y is largest" : "z is largest"
    print "x =", x, ", y =", y, ", z =", z, ", result =", result
    
    x = 5
    y = 20
    z = 15
    result = x > y ? "x is largest" : y > z ? "y is largest" : "z is largest"
    print "x =", x, ", y =", y, ", z =", z, ", result =", result
    print ""
    
    # Ternary with arithmetic operations
    num = 7
    result = num % 2 == 0 ? num * 2 : num * 3
    print "num =", num, ", num % 2 == 0 ? num * 2 : num * 3 =", result
    
    num = 8
    result = num % 2 == 0 ? num * 2 : num * 3
    print "num =", num, ", num % 2 == 0 ? num * 2 : num * 3 =", result
    print ""
    
    # Ternary with string concatenation
    prefix = "Mr"
    name = "Smith"
    full_name = prefix == "Mr" ? prefix ". " name : prefix "s. " name
    print "prefix =", prefix, ", name =", name, ", full_name =", full_name
    
    prefix = "Mrs"
    full_name = prefix == "Mr" ? prefix ". " name : prefix "s. " name
    print "prefix =", prefix, ", name =", name, ", full_name =", full_name
    print ""
    
    # Ternary with function calls
    value = 5
    result = value > 0 ? sqrt(value) : 0
    print "value =", value, ", value > 0 ? sqrt(value) : 0 =", result
    
    value = -5
    result = value > 0 ? sqrt(value) : 0
    print "value =", value, ", value > 0 ? sqrt(value) : 0 =", result
    print ""
    
    # Ternary precedence test (ternary has lower precedence than assignment)
    x = 1
    y = 2
    z = x > 0 ? y = 3 : y = 4
    print "After: x =", x, ", y =", y, ", z =", z
    print "Note: assignment happens, then ternary evaluates to assigned value"
}

