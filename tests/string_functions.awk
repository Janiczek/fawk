# Test: String Functions

BEGIN {
    s = "Hello World"
    print "Original:", s
    print "toupper:", toupper(s)
    print "tolower:", tolower(s)
    print "substr(s,1,5):", substr(s, 1, 5)
    print "substr(s,7):", substr(s, 7)
    
    # sprintf
    result = sprintf("Number: %d, Float: %.2f", 42, 3.14)
    print "sprintf:", result
    
    # Note: sub and gsub with explicit target not fully supported yet
    # Testing with string functions only
    print "sub count:", sub("foo", "baz", "foo bar foo")
    print "gsub count:", gsub("foo", "baz", "foo bar foo")
}

