# Test: Chained field assignments
# Test that assignments can reference other fields

BEGIN {
    print "Test: Chained field assignments"
    print "--------------------------------------"
}

{
    print "Original: $0 =", $0
    print "  $1 =", $1, ", $2 =", $2, ", $3 =", $3
    
    # Chain: $2 uses $1, $3 uses $2
    $2 = $1 * 2
    $3 = $2 * 2
    
    print "After $2 = $1 * 2; $3 = $2 * 2:"
    print "  $0:", $0
    print "  $1 =", $1, ", $2 =", $2, ", $3 =", $3
    print ""
}

