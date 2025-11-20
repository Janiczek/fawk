# Test: Match Operators (~ and !~)

BEGIN {
    print "Test: Match Operators (~ and !~)"
    print "--------------------------------------"
    print "  'hello' ~ 'ell':", "hello" ~ "ell"
    print "  'hello' ~ 'xyz':", "hello" ~ "xyz"
    print "  'test123' ~ '[0-9]+':", "test123" ~ "[0-9]+"
    print "  'test123' ~ '^test':", "test123" ~ "^test"
    print "  'test123' ~ '123$':", "test123" ~ "123$"
    print ""
    
    print "Negated Match (!~):"
    print "--------------------------------------"
    print "  'hello' !~ 'xyz':", "hello" !~ "xyz"
    print "  'hello' !~ 'ell':", "hello" !~ "ell"
    print "  'abc' !~ '[0-9]+':", "abc" !~ "[0-9]+"
}

