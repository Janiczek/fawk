# Test: High Precision Arithmetic Operations

BEGIN {
    PREC = 100
    
    # High precision division
    a = 1
    b = 3
    result = a / b
    printf("1/3 with PREC=100:\n%.20f\n", result)
    
    # High precision multiplication
    pi = 4 * atan2(1, 1)
    printf("\nPi with PREC=100:\n%.20f\n", pi)
    
    # High precision square root
    sqrt2 = sqrt(2)
    printf("\nsqrt(2) with PREC=100:\n%.20f\n", sqrt2)
}

