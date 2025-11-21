# Test: Increment and Decrement Operators

BEGIN {
    print "Test: Increment and Decrement Operators"
    print "--------------------------------------"
    
    # Prefix increment
    x = 5
    print "Prefix increment:"
    print "  x =", x
    print "  ++x =", ++x
    print "  x =", x
    print ""
    
    # Prefix decrement
    y = 10
    print "Prefix decrement:"
    print "  y =", y
    print "  --y =", --y
    print "  y =", y
    print ""
    
    # Postfix increment
    a = 3
    print "Postfix increment:"
    print "  a =", a
    print "  a++ =", a++
    print "  a =", a
    print ""
    
    # Postfix decrement
    b = 7
    print "Postfix decrement:"
    print "  b =", b
    print "  b-- =", b--
    print "  b =", b
    print ""
    
    # Using in expressions
    c = 5
    d = 10
    print "In expressions:"
    print "  c =", c, ", d =", d
    print "  c + ++d =", c + ++d
    print "  c =", c, ", d =", d
    print ""
    
    e = 5
    f = 10
    print "  e =", e, ", f =", f
    print "  e + f++ =", e + f++
    print "  e =", e, ", f =", f
    print ""
    
    # Multiple increments
    g = 0
    print "Multiple increments:"
    print "  g =", g
    print "  ++g =", ++g
    print "  ++g =", ++g
    print "  g++ =", g++
    print "  g =", g
    print ""
    
    # Array elements
    arr[0] = 10
    arr[1] = 20
    print "Array elements:"
    print "  arr[0] =", arr[0]
    print "  ++arr[0] =", ++arr[0]
    print "  arr[0] =", arr[0]
    print "  arr[1]++ =", arr[1]++
    print "  arr[1] =", arr[1]
    print ""
    
    # Precedence test
    h = 5
    i = 10
    print "Precedence:"
    print "  h =", h, ", i =", i
    print "  -++h =", -++h
    print "  h =", h
    print "  -i++ =", -i++
    print "  i =", i
}

