BEGIN {
    # Test changing FS
    FS = ":"
}

{
    print "Fields:", NF
    print "Field 1:", $1
    print "Field 2:", $2
    print "Field 3:", $3
}

