# Test: C-style for loop

BEGIN {
    print "Test: C-style for loop"
    print "--------------------------------------"
    
    # Basic for loop
    print "Count 0 to 4:"
    for (i = 0; i < 5; i = i + 1) {
        print "  i =", i
    }
    print ""
    
    # For loop with step
    print "Count by 2s from 0 to 8:"
    for (j = 0; j <= 8; j = j + 2) {
        print "  j =", j
    }
    print ""
    
    # For loop with break
    print "Loop with break at 3:"
    for (k = 0; k < 10; k = k + 1) {
        if (k == 3) {
            break
        }
        print "  k =", k
    }
    print ""
    
    # For loop with continue
    print "Loop with continue (skip evens):"
    for (m = 0; m < 6; m = m + 1) {
        if (m % 2 == 0) {
            continue
        }
        print "  m =", m
    }
    print ""
    
    # Nested for loops
    print "Nested loops:"
    for (x = 0; x < 3; x = x + 1) {
        for (y = 0; y < 2; y = y + 1) {
            print "  x =", x, "y =", y
        }
    }
}

