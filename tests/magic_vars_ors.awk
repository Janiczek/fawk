BEGIN {
    # Default ORS is newline
    print "line1"
    print "line2"
    
    # Change ORS to custom separator
    ORS = " <END> "
    print "line3"
    print "line4"
    
    # Change ORS to double newline
    ORS = "\n\n"
    print "line5"
    print "line6"
}

