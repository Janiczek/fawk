# Test: Security pattern from user example

BEGIN {
    print "Monitoring web requests..."
    print "----------------------------"
}

# Detect suspicious DELETE requests to admin pages
/admin\.html/ && $2 == "DELETE" {
    print "Hacker Alert!";
}

# Also test variations
/admin/ && $2 == "POST" && $3 == "unauthorized" {
    print "Unauthorized POST to admin area!";
}

# Normal requests should pass through
/\.html/ && $2 == "GET" {
    print "Normal request:", $1, $2;
}

END {
    print "----------------------------"
    print "Security monitoring complete"
}

