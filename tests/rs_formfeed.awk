BEGIN {
    RS = "\f"
}

{
    print "Page " NR ":"
    print $0
    print "---"
}

