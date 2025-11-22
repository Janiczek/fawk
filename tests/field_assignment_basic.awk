# Test: Basic field assignment
# Test that $2 = value updates both $2 and $0

BEGIN {
    print "Test: Basic field assignment"
    print "--------------------------------------"
}

{
    print "Before assignment:"
    print "  $0:", $0
    print "  $2:", $2
    print "  NF:", NF
    
    $2 = "modified"
    
    print "After $2 = \"modified\":"
    print "  $0:", $0
    print "  $2:", $2
    print "  NF:", NF
    print ""
}

