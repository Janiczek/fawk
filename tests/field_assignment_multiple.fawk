# Test: Multiple field assignments
# Test assigning to multiple fields in sequence

BEGIN {
    print "Test: Multiple field assignments"
    print "--------------------------------------"
}

{
    print "Original: $0 =", $0
    print "  $1 =", $1, ", $2 =", $2, ", $3 =", $3
    
    $1 = "first"
    $2 = "second"
    $3 = "third"
    
    print "After assignments:"
    print "  $0:", $0
    print "  $1 =", $1, ", $2 =", $2, ", $3 =", $3
    print ""
}

