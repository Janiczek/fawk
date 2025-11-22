# Test: Nested ternary operators (right-associative)

BEGIN {
    print "Test: Nested ternary operators"
    print "--------------------------------------"
    
    # Test right-associativity: a ? b : c ? d : e should be a ? b : (c ? d : e)
    a = 1
    b = 2
    c = 0
    d = 3
    e = 4
    
    # This should evaluate as: a ? b : (c ? d : e)
    # Since a=1 (truthy), result should be b=2
    result = a ? b : c ? d : e
    print "a =", a, ", b =", b, ", c =", c, ", d =", d, ", e =", e
    print "a ? b : c ? d : e =", result, "(should be", b, "due to right-associativity)"
    print ""
    
    # Test with a=0, c=1: should evaluate as a ? b : (c ? d : e) = 0 ? b : (1 ? d : e) = d
    a = 0
    c = 1
    result = a ? b : c ? d : e
    print "a =", a, ", b =", b, ", c =", c, ", d =", d, ", e =", e
    print "a ? b : c ? d : e =", result, "(should be", d, "due to right-associativity)"
    print ""
    
    # Test with a=0, c=0: should evaluate as a ? b : (c ? d : e) = 0 ? b : (0 ? d : e) = e
    a = 0
    c = 0
    result = a ? b : c ? d : e
    print "a =", a, ", b =", b, ", c =", c, ", d =", d, ", e =", e
    print "a ? b : c ? d : e =", result, "(should be", e, "due to right-associativity)"
    print ""
    
    # Test nested in true branch: a ? (b ? c : d) : e
    a = 1
    b = 1
    c = 10
    d = 20
    e = 30
    result = a ? b ? c : d : e
    print "a =", a, ", b =", b, ", c =", c, ", d =", d, ", e =", e
    print "a ? b ? c : d : e =", result, "(should be", c, "since a and b are truthy)"
    print ""
    
    # Test nested in true branch with b=0
    a = 1
    b = 0
    result = a ? b ? c : d : e
    print "a =", a, ", b =", b, ", c =", c, ", d =", d, ", e =", e
    print "a ? b ? c : d : e =", result, "(should be", d, "since a is truthy but b is falsy)"
    print ""
    
    # Test nested in true branch with a=0
    a = 0
    b = 1
    result = a ? b ? c : d : e
    print "a =", a, ", b =", b, ", c =", c, ", d =", d, ", e =", e
    print "a ? b ? c : d : e =", result, "(should be", e, "since a is falsy)"
}

