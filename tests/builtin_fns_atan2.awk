# Test: atan2() function

BEGIN {
    print "Test: atan2() function"
    print "--------------------------------------"
    
    # Basic test (should give pi/4)
    result1 = atan2(1, 1)
    print "  atan2(1, 1):", result1
    
    # Test with different values
    result2 = atan2(1, 0)
    print "  atan2(1, 0):", result2
    
    result3 = atan2(0, 1)
    print "  atan2(0, 1):", result3
    
    result4 = atan2(-1, 1)
    print "  atan2(-1, 1):", result4
    
    result5 = atan2(1, -1)
    print "  atan2(1, -1):", result5
    
    # Test with larger values
    result6 = atan2(10, 5)
    print "  atan2(10, 5):", result6
}

