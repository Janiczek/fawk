# Test: Arbitrary Precision Arithmetic - Calculate Pi
# This test is compatible with gawk -M

BEGIN {
    PREC = 333
    pi = 4 * atan2(1, 1)
    printf("%.99f\n", pi)
}

