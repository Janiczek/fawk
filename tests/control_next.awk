# Test: next statement

BEGIN {
    print "Test: next statement"
    print "--------------------------------------"
}

{
    print "Line", NR, "start"
    
    if (NR == 2 || NR == 4) {
        print "  Skipping line", NR
        next
    }
    
    print "  Processing line", NR
    print "Line", NR, "end"
}

END {
    print "--------------------------------------"
    print "Total lines:", NR
}

