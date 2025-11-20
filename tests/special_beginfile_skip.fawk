BEGINFILE {
    if (FILENAME ~ /input1$/) {
        print "Skipping file:", FILENAME
        nextfile
    }
    print "Processing file:", FILENAME
}

{
    print "  Line", FNR ":", $0
}

ENDFILE {
    print "Done with:", FILENAME
}

