BEGIN {
    # CONVFMT is used for number-to-string conversion in concatenation
    x = 3.14159265
    
    # Default CONVFMT
    s = x ""
    print "Default CONVFMT (%.6g):", s
    
    # Change CONVFMT to show more decimals
    CONVFMT = "%.10f"
    s = x ""
    print "CONVFMT=%.10f:", s
    
    # Change to scientific notation
    CONVFMT = "%.2e"
    s = x ""
    print "CONVFMT=%.2e:", s
}

