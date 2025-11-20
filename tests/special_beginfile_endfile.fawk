BEGIN {
    print "BEGIN: Starting processing"
}

BEGINFILE {
    print "BEGINFILE: Starting file", FILENAME, "at NR=" NR
}

{
    print "Line", FNR, "of", FILENAME ":", $0
}

ENDFILE {
    print "ENDFILE: Finished file", FILENAME, "with", FNR, "lines, total NR=" NR
}

END {
    print "END: Processed", NR, "total lines"
}

