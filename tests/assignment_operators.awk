# Test: Compound Assignment Operators

BEGIN {
    # Test += operator
    x = 5
    x += 3
    print "x += 3 (starting from 5) =", x
    
    # Test -= operator
    y = 10
    y -= 4
    print "y -= 4 (starting from 10) =", y
    
    # Test *= operator
    z = 3
    z *= 4
    print "z *= 4 (starting from 3) =", z
    
    # Test /= operator
    w = 20
    w /= 5
    print "w /= 5 (starting from 20) =", w
    
    # Test with undefined variable (should default to 0)
    a += 5
    print "a += 5 (undefined variable) =", a
    
    # Test with array elements
    arr[1] = 10
    arr[1] += 5
    print "arr[1] += 5 (starting from 10) =", arr[1]
    
    arr[2] = 20
    arr[2] -= 8
    print "arr[2] -= 8 (starting from 20) =", arr[2]
    
    arr[3] = 3
    arr[3] *= 7
    print "arr[3] *= 7 (starting from 3) =", arr[3]
    
    arr[4] = 30
    arr[4] /= 6
    print "arr[4] /= 6 (starting from 30) =", arr[4]
    
    # Test with field access
    $0 = "10 20 30"
    $1 += 5
    print "$1 += 5 (starting from 10) =", $1
    
    $2 -= 8
    print "$2 -= 8 (starting from 20) =", $2
    
    $3 *= 2
    print "$3 *= 2 (starting from 30) =", $3
    
    # Test chaining (multiple assignments)
    b = 2
    b += 3
    b *= 2
    print "b = 2; b += 3; b *= 2 =", b
    
    # Test with negative numbers
    c = -5
    c += 10
    print "c += 10 (starting from -5) =", c
    
    d = 10
    d -= 15
    print "d -= 15 (starting from 10) =", d
}

