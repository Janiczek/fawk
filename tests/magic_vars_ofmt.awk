BEGIN {
    # Default OFMT is %.6g
    x = 3.14159265358979
    print "Default OFMT:", x
    
    # Change OFMT to show more precision
    OFMT = "%.10f"
    print "OFMT=%.10f:", x
    
    # Change to scientific notation
    OFMT = "%.3e"
    print "OFMT=%.3e:", x
    
    # Test with integer that looks like float
    y = 42.0
    OFMT = "%.6g"
    print "Integer as float (%.6g):", y
}

