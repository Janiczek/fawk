BEGIN {
    RS = "[,;:]"
}

{
    print "Record: [" $0 "] Terminator: [" RT "]"
}

