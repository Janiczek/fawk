# Test: exit statement

BEGIN {
    print "BEGIN block"
    x = 5
}

{
    print "Processing line:", NR
    if (NR == 3) {
        print "Exiting with code 0"
        exit 0
    }
}

END {
    print "END block"
    print "x =", x
}

