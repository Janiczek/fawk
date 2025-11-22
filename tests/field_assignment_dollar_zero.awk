# Test: Assigning to $0
# Test that $0 = value re-splits the line into fields

BEGIN {
    print "Test: Assigning to $0"
    print "--------------------------------------"
}

{
    print "Original:"
    print "  $0:", $0
    print "  NF:", NF
    print "  $1:", $1, "$2:", $2, "$3:", $3
    
    $0 = "new first new second new third"
    
    print "After $0 = \"new first new second new third\":"
    print "  $0:", $0
    print "  NF:", NF
    print "  $1:", $1, "$2:", $2, "$3:", $3
    print ""
}

