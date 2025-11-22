# Test: substr() function

BEGIN {
    print "Test: substr() function"
    print "--------------------------------------"
    
    s = "Hello World"
    print "  Original string:", s
    print "  substr(s, 1, 5):", substr(s, 1, 5)
    print "  substr(s, 7):", substr(s, 7)
    print "  substr(s, 1, 11):", substr(s, 1, 11)
    print "  substr(s, 7, 5):", substr(s, 7, 5)
    
    print ""
    
    # Edge cases
    print "  Edge cases:"
    print "  substr(\"abc\", 1, 0):", substr("abc", 1, 0)
    print "  substr(\"abc\", 2, 10):", substr("abc", 2, 10)
    print "  substr(\"abc\", 10, 5):", substr("abc", 10, 5)
    print "  substr(\"\", 1, 1):", substr("", 1, 1)
}

