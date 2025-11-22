# Test: exp() function

BEGIN {
    print "Test: exp() function"
    print "--------------------------------------"
    
    # Basic test (e^0 = 1)
    result1 = exp(0)
    print "  exp(0):", result1
    
    # Test with 1 (should be e)
    result2 = exp(1)
    print "  exp(1):", result2
    
    # Test with 2
    result3 = exp(2)
    print "  exp(2):", result3
    
    # Test with negative value
    result4 = exp(-1)
    print "  exp(-1):", result4
    
    # Test with small value
    result5 = exp(0.5)
    print "  exp(0.5):", result5
}

