# Test: sin() function

BEGIN {
    print "Test: sin() function"
    print "--------------------------------------"
    
    # Basic test
    result1 = sin(0)
    print "  sin(0):", result1
    
    # Test with pi/2 (should be 1)
    pi = 3.141592653589793
    result2 = sin(pi / 2)
    print "  sin(pi/2):", result2
    
    # Test with pi (should be 0)
    result3 = sin(pi)
    print "  sin(pi):", result3
    
    # Test with 2*pi (should be 0)
    result4 = sin(2 * pi)
    print "  sin(2*pi):", result4
    
    # Test with negative value
    result5 = sin(-pi / 2)
    print "  sin(-pi/2):", result5
}

