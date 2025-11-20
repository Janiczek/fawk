# Test: Field and record separators (FS, OFS, RS, ORS)

BEGIN {
    print "Test: Field and record separators"
    print "--------------------------------------"
    print "  FS:", FS
    print "  OFS:", OFS
    print "  RS:", RS
    print "  ORS:", length(ORS), "bytes"
    print ""
    
    # Change OFS
    OFS = "|"
    print "Test: Modified OFS"
    print "--------------------------------------"
    print "  a", "b", "c"
    OFS = " "
}

