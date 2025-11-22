# Test: Field assignment with custom OFS
# Test that $0 reconstruction uses OFS

BEGIN {
    OFS = ":"
    print "Test: Field assignment with custom OFS"
    print "--------------------------------------"
    print "OFS set to ':'"
    print ""
}

{
    print "Before assignment:"
    print "  $0 = " $0
    print "  $2 = " $2
    
    $2 = "modified"
    
    print "After $2 = \"modified\":"
    print "  $0 = " $0
    print "  $2 = " $2
    print ""
}

