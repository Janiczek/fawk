BEGIN {
    x = "A"
    x = x "B"
    print x "C"
    
    # Multiple string concatenation
    print "A" "B" "C" "D"
    
    # Numeric variable concatenation
    a = 1
    b = 2
    print a b
    
    # Mixed types concatenation
    print "num:" 42 " end"
}