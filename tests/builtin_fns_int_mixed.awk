# Test: int() function with mixed alphanumeric strings

BEGIN {
    print "Test: int() function with mixed alphanumeric strings"
    print "--------------------------------------"
    
    # Test with string starting with integer
    result1 = int("123abc")
    print "  int(\"123abc\"):", result1
    
    # Test with string starting with float
    result2 = int("123.45abc")
    print "  int(\"123.45abc\"):", result2
    
    # Test with string starting with negative integer
    result3 = int("-456xyz")
    print "  int(\"-456xyz\"):", result3
    
    # Test with string starting with negative float
    result4 = int("-456.78xyz")
    print "  int(\"-456.78xyz\"):", result4
    
    # Test with string starting with zero
    result5 = int("0abc")
    print "  int(\"0abc\"):", result5
    
    # Test with string starting with zero point something
    result6 = int("0.5abc")
    print "  int(\"0.5abc\"):", result6
    
    # Test with pure numeric string (should still work)
    result7 = int("123")
    print "  int(\"123\"):", result7
    
    # Test with pure float string (should still work)
    result8 = int("123.45")
    print "  int(\"123.45\"):", result8
}

