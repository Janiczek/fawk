# Test: Edge cases for field assignment
# Test various edge cases

BEGIN {
    print "Test: Edge cases for field assignment"
    print "--------------------------------------"
}

{
    # Test 1: Assign to first field
    print "Test 1: Assign to $1"
    print "  Before: $0 =", $0, ", $1 =", $1
    $1 = "FIRST"
    print "  After: $0 =", $0, ", $1 =", $1
    print ""
    
    # Test 2: Assign to last field
    print "Test 2: Assign to last field ($" NF ")"
    print "  Before: $0 =", $0, ", $" NF " =", $(NF)
    $(NF) = "LAST"
    print "  After: $0 =", $0, ", $" NF " =", $(NF)
    print ""
    
    # Test 3: Assign to very high field number
    print "Test 3: Assign to $10"
    print "  Before: NF =", NF, ", $0 =", $0
    $10 = "TENTH"
    print "  After: NF =", NF, ", $0 =", $0
    print "  $10 =", $10
    print ""
    
    # Test 4: Multiple assignments with expressions
    print "Test 4: Multiple assignments with expressions"
    print "  Before: $1 =", $1, ", $2 =", $2
    $1 = $1 * 2
    $2 = $2 + 10
    print "  After: $1 =", $1, ", $2 =", $2, ", $0 =", $0
    print ""
    
    # Test 5: Assign empty string
    print "Test 5: Assign empty string to field"
    print "  Before: $2 =", $2
    $2 = ""
    print "  After: $2 =", $2, "(empty), $0 =", $0
    print ""
    
    print "--------------------------------------"
    print ""
}

