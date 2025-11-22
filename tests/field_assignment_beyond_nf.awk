# Test: Assigning to fields beyond NF
# Test that assigning to $5 when NF=3 extends the fields array

BEGIN {
    print "Test: Assigning to fields beyond NF"
    print "--------------------------------------"
}

{
    print "Before assignment:"
    print "  $0:", $0
    print "  NF:", NF
    print "  $1:", $1, "$2:", $2, "$3:", $3
    
    $5 = "fifth"
    
    print "After $5 = \"fifth\":"
    print "  $0:", $0
    print "  NF:", NF
    print "  $1:", $1, "$2:", $2, "$3:", $3, "$4:", $4, "$5:", $5
    print ""
}

