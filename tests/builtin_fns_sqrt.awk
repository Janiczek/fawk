# Test: sqrt() function

BEGIN {
    print "Test: sqrt() function"
    print "--------------------------------------"
    
    # Basic test
    result1 = sqrt(16)
    print "  sqrt(16):", result1
    
    # Test with 1
    result2 = sqrt(1)
    print "  sqrt(1):", result2
    
    # Test with 0
    result3 = sqrt(0)
    print "  sqrt(0):", result3
    
    # Test with perfect square
    result4 = sqrt(25)
    print "  sqrt(25):", result4
    
    # Test with non-perfect square
    result5 = sqrt(2)
    print "  sqrt(2):", result5
    
    # Test with decimal
    result6 = sqrt(0.25)
    print "  sqrt(0.25):", result6
}

