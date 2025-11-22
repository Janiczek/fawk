# Test: cos() function

BEGIN {
    print "Test: cos() function"
    print "--------------------------------------"
    
    # Basic test
    result1 = cos(0)
    print "  cos(0):", result1
    
    # Test with pi/2 (should be close to 0)
    pi = 3.141592653589793
    result2 = cos(pi / 2)
    print "  cos(pi/2):", result2
    
    # Test with pi (should be -1)
    result3 = cos(pi)
    print "  cos(pi):", result3
    
    # Test with 2*pi (should be 1)
    result4 = cos(2 * pi)
    print "  cos(2*pi):", result4
    
    # Test with negative value
    result5 = cos(-pi / 3)
    print "  cos(-pi/3):", result5
}

