BEGIN {
    # Test default SUBSEP value (octal 034 = ASCII 28 = hex 1C)
    print "Default SUBSEP length:", length(SUBSEP)
    
    # Create a multi-dimensional array using SUBSEP
    arr[1 SUBSEP 2] = "one-two"
    arr[1 SUBSEP 3] = "one-three"
    arr[2 SUBSEP 1] = "two-one"
    
    # Print values
    print "arr[1,2] via SUBSEP:", arr[1 SUBSEP 2]
    print "arr[1,3] via SUBSEP:", arr[1 SUBSEP 3]
    print "arr[2,1] via SUBSEP:", arr[2 SUBSEP 1]
    
    # Change SUBSEP
    SUBSEP = ","
    print "Changed SUBSEP to:", SUBSEP
    
    # Create new entries with new SUBSEP
    arr2[1 SUBSEP 2] = "comma-sep"
    print "arr2[1,2] with comma SUBSEP:", arr2[1 SUBSEP 2]
    
    # Test with double colon
    SUBSEP = "::"
    arr3["x" SUBSEP "y"] = "double-colon"
    print "arr3[x,y] with :: SUBSEP:", arr3["x" SUBSEP "y"]
}
