# Test: Regex pattern matching

BEGIN {
    print "Test: Regex pattern matching"
    print "--------------------------------------"
}

# Match lines starting with "product"
/^product/ {
    print "Found product line:", $0
}

# Match lines with "error" or "warning" (case-insensitive)
# GAWK doesn't support /pattern/i syntax, so we use tolower() for compatibility
tolower($0) ~ /error|warning/ {
    print "Found issue:", $0
}

END {
    print "Pattern matching completed"
}

