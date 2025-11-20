# Test: Pattern expressions with operators

BEGIN {
    print "Test: Pattern expressions with operators"
    print "=========================================="
}

# Test 1: Regex && comparison
/admin/ && $2 == "DELETE" {
    print "Security alert: DELETE on admin path - Line:", NR
}

# Test 2: Regex || regex
/error/ || /warning/ {
    print "Issue found:", $0
}

# Test 3: Field comparison && another field comparison
$1 == "user" && $3 > 100 {
    print "High value user:", $2, "with value", $3
}

# Test 4: Regex && field comparison with operator
/product/ && $3 >= 50 {
    print "Expensive product:", $2, "at price", $3
}

# Test 5: Negation with field
$1 != "comment" {
    print "Non-comment line:", $0
}

# Test 6: Complex boolean expression
($1 == "order" || $1 == "sale") && $3 > 100 {
    print "Large transaction:", $1, $2, $3
}

# Test 7: Match operator in pattern
$2 ~ "^admin" && $3 != "" {
    print "Admin with data:", $2, $3
}

# Test 8: Not match operator in pattern
$1 !~ "^#" && NF > 2 {
    print "Valid data line with", NF, "fields:", $0
}

END {
    print "Pattern operator tests completed"
}

