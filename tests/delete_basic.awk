# Test: Basic delete operations
# Test deleting array elements

BEGIN {
    print "Test: Basic delete operations"
    print "--------------------------------------"
    
    # Test 1: Delete array element
    arr[1] = 10
    arr[2] = 20
    arr[3] = 30
    
    print "Before delete:"
    print "  arr[1] =", arr[1]
    print "  arr[2] =", arr[2]
    print "  arr[3] =", arr[3]
    print "  length(arr) =", length(arr)
    
    delete arr[2]
    
    print "After delete arr[2]:"
    print "  arr[1] =", arr[1]
    print "  arr[2] =", arr[2]
    print "  arr[3] =", arr[3]
    print "  length(arr) =", length(arr)
    
    # Test membership
    if (2 in arr) {
        print "  2 is in arr (ERROR!)"
    } else {
        print "  2 is NOT in arr (correct)"
    }
    
    if (1 in arr) {
        print "  1 is in arr (correct)"
    } else {
        print "  1 is NOT in arr (ERROR!)"
    }
    
    print ""
    
    # Test 2: Delete non-existent element (should not error)
    print "Test 2: Delete non-existent element"
    delete arr[99]
    print "  delete arr[99] succeeded - no error"
    print "  length(arr) =", length(arr)
    print ""
    
    # Test 3: Delete multiple elements
    print "Test 3: Delete multiple elements"
    arr2[1] = "a"
    arr2[2] = "b"
    arr2[3] = "c"
    arr2[4] = "d"
    print "  Before: length =", length(arr2)
    delete arr2[1]
    delete arr2[3]
    print "  After deleting [1] and [3]: length =", length(arr2)
    print "  arr2[2] =", arr2[2]
    print "  arr2[4] =", arr2[4]
    print ""
}

