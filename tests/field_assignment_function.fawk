# Test: Field assignment with functions
# Test that $2 = log($2) works correctly

BEGIN {
    print "Test: Field assignment with functions"
    print "--------------------------------------"
}

{
    print "Before: $2 =", $2
    $2 = log($2)
    print "After $2 = log($2):"
    print "  $0:", $0
    print "  $2:", $2
    print ""
}

