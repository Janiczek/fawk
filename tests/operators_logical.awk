# Test: Logical Operators

BEGIN {
    print "Test: Logical Operators"
    print "--------------------------------------"
    print "  1 && 1:", 1 && 1
    print "  1 && 0:", 1 && 0
    print "  0 && 0:", 0 && 0
    print "  1 || 0:", 1 || 0
    print "  0 || 0:", 0 || 0
    print "  !1:", !1
    print "  !0:", !0
    print ""
    
    print "Complex Expressions:"
    print "--------------------------------------"
    print "  (5 > 3) && (2 < 4):", (5 > 3) && (2 < 4)
    print "  (5 > 3) || (2 > 4):", (5 > 3) || (2 > 4)
    print "  (5 < 3) || (2 > 4):", (5 < 3) || (2 > 4)
    print ""
    
    x = 5
    y = 10
    z = 15
    print "  x = 5, y = 10, z = 15"
    print "  x < y && y < z:", x < y && y < z
    print "  (x * 2 == y) && (y + 5 == z):", (x * 2 == y) && (y + 5 == z)
}

