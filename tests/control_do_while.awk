# Test: do-while loop

BEGIN {
    print "Test: do-while loop"
    print "--------------------------------------"
    
    # Basic do-while
    print "Basic do-while (count 0 to 4):"
    i = 0
    do {
        print "  i =", i
        i = i + 1
    } while (i < 5)
    print ""
    
    # Do-while executes at least once
    print "Do-while with false condition (executes once):"
    j = 10
    do {
        print "  j =", j
        j = j + 1
    } while (j < 5)
    print ""
    
    # Do-while with break
    print "Do-while with break at 3:"
    k = 0
    do {
        if (k == 3) {
            break
        }
        print "  k =", k
        k = k + 1
    } while (k < 10)
    print ""
    
    # Do-while with continue
    print "Do-while with continue (skip evens):"
    m = 0
    do {
        m = m + 1
        if (m % 2 == 0) {
            continue
        }
        print "  m =", m
    } while (m < 6)
}

