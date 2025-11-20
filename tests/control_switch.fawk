# Test: switch statement

BEGIN {
    print "Test: switch statement"
    print "--------------------------------------"
    
    # Basic switch
    print "Testing switch with 'a':"
    c = "a"
    switch (c) {
    case "a":
        print "  Got 'a'"
        break
    case "b":
        print "  Got 'b'"
        break
    default:
        print "  Got something else"
        break
    }
    print ""
    
    # Switch with numeric values
    print "Testing switch with numbers:"
    for (i = 1; i <= 4; i = i + 1) {
        print "  i =", i, ":"
        switch (i) {
        case 1:
            print "    One"
            break
        case 2:
            print "    Two"
            break
        case 3:
            print "    Three"
            break
        default:
            print "    Other"
            break
        }
    }
    print ""
    
    # Switch with default
    print "Testing switch with default:"
    x = "z"
    switch (x) {
    case "a":
        print "  Case a"
        break
    case "b":
        print "  Case b"
        break
    default:
        print "  Default case: x =", x
        break
    }
    print ""
    
    # Switch with multiple statements per case
    print "Testing switch with multiple statements:"
    val = 2
    switch (val) {
    case 1:
        print "  First line of case 1"
        print "  Second line of case 1"
        break
    case 2:
        print "  First line of case 2"
        print "  Second line of case 2"
        x = val * 10
        print "  x =", x
        break
    default:
        print "  Default"
        break
    }
}

