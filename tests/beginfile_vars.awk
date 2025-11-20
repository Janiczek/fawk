# Test that variables persist across files
BEGIN {
    total_files = 0
    total_lines = 0
}

BEGINFILE {
    total_files = total_files + 1
    file_lines = 0
}

{
    file_lines = file_lines + 1
    total_lines = total_lines + 1
}

ENDFILE {
    print "File", total_files, "had", file_lines, "lines"
}

END {
    print "Processed", total_files, "files with", total_lines, "total lines"
}

