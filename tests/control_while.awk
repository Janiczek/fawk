# Test: while loop

BEGIN {
    print "Test: while loop"
    print "--------------------------------------"
    
    # Basic while loop
    print "Basic while (count 0 to 4):"
    i = 0
    while (i < 5) {
        print "  i =", i
        i = i + 1
    }
    print ""
    
    # While loop with false condition (doesn't execute)
    print "While with false condition (doesn't execute):"
    j = 10
    while (j < 5) {
        print "  j =", j
        j = j + 1
    }
    print "  j remains", j
    print ""
    
    # While loop with break
    print "While with break at 3:"
    k = 0
    while (k < 10) {
        if (k == 3) {
            break
        }
        print "  k =", k
        k = k + 1
    }
    print ""
    
    # While loop with continue
    print "While with continue (skip evens):"
    m = 0
    while (m < 6) {
        if (m % 2 == 0) {
            m = m + 1
            continue
        }
        print "  m =", m
        m = m + 1
    }
    print ""
    
    # Nested while loops
    print "Nested while loops:"
    x = 0
    while (x < 3) {
        y = 0
        while (y < 2) {
            print "  x =", x, "y =", y
            y = y + 1
        }
        x = x + 1
    }
}

