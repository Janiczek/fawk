# Test: sprintf() function

BEGIN {
    print "Test: sprintf() function"
    print "--------------------------------------"
    
    # Integer formatting
    result1 = sprintf("Number: %d", 42)
    print "  sprintf(\"Number: %%d\", 42):", result1
    
    # Float formatting
    result2 = sprintf("Float: %.2f", 3.14159)
    print "  sprintf(\"Float: %%.2f\", 3.14159):", result2
    
    # String formatting
    result3 = sprintf("String: %s", "hello")
    print "  sprintf(\"String: %%s\", \"hello\"):", result3
    
    # Multiple arguments
    result4 = sprintf("Multiple: %d %s %.1f", 10, "test", 2.5)
    print "  sprintf(\"Multiple: %%d %%s %%.1f\", 10, \"test\", 2.5):", result4
    
    # Width formatting
    result5 = sprintf("Width: %10d", 42)
    print "  sprintf(\"Width: %%10d\", 42):", result5
    
    # Precision formatting
    result6 = sprintf("Precision: %.5f", 1.23456789)
    print "  sprintf(\"Precision: %%.5f\", 1.23456789):", result6
    
    # Percent sign
    result7 = sprintf("Percent: %%")
    print "  sprintf(\"Percent: %%%%\"):", result7
}

