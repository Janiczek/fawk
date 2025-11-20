BEGIN {
    # Default OFS is space
    print "Default OFS:", "a", "b", "c"
    
    # Change OFS to comma
    OFS = ","
    print "OFS=comma:", "x", "y", "z"
    
    # Change OFS to tab
    OFS = "\t"
    print "OFS=tab:", "1", "2", "3"
    
    # Change OFS to custom separator
    OFS = " | "
    print "OFS=pipe:", "foo", "bar", "baz"
}

