# Test: Edge cases for delete (GAWK compatible)
# Test various edge cases for standard delete operations

BEGIN {
    print "Test: Edge cases for delete (GAWK compatible)"
    print "--------------------------------------"
    
    # Test 1: Delete from empty array
    print "Test 1: Delete from empty array"
    empty[1] = 5
    delete empty[1]
    print "  After delete empty[1]: length =", length(empty)
    delete empty[2]
    print "  After delete empty[2] (non-existent): length =", length(empty)
    print ""
    
    # Test 2: Delete array element with string key
    print "Test 2: Delete array element with string key"
    assoc["key1"] = "value1"
    assoc["key2"] = "value2"
    assoc["key3"] = "value3"
    print "  Before: length =", length(assoc)
    delete assoc["key2"]
    print "  After delete assoc[key2]: length =", length(assoc)
    print "  assoc[key1] =", assoc["key1"]
    print "  assoc[key2] =", assoc["key2"]
    print "  assoc[key3] =", assoc["key3"]
    print ""
    
    # Test 3: Multiple deletes in sequence
    print "Test 3: Multiple deletes in sequence"
    multi[1] = "a"
    multi[2] = "b"
    multi[3] = "c"
    multi[4] = "d"
    multi[5] = "e"
    print "  Before: length =", length(multi)
    delete multi[2]
    delete multi[4]
    delete multi[1]
    print "  After deleting [2], [4], [1]: length =", length(multi)
    print "  multi[3] =", multi[3]
    print "  multi[5] =", multi[5]
    print ""
    
    # Test 4: Delete non-existent element multiple times
    print "Test 4: Delete non-existent element multiple times"
    test[1] = 10
    print "  Before: length =", length(test)
    delete test[99]
    delete test[99]
    delete test[99]
    print "  After deleting [99] three times: length =", length(test)
    print "  test[1] =", test[1]
    print ""
    
    # Test 5: Delete and re-add
    print "Test 5: Delete and re-add"
    dynamic[1] = "first"
    dynamic[2] = "second"
    print "  Before delete: length =", length(dynamic)
    delete dynamic[1]
    print "  After delete [1]: length =", length(dynamic)
    dynamic[1] = "new_first"
    print "  After re-adding [1]: length =", length(dynamic)
    print "  dynamic[1] =", dynamic[1]
    print "  dynamic[2] =", dynamic[2]
    print ""
}

