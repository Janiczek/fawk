# Requires arbitrary precision (PREC)
BEGIN {
  x = 5^4^3^2
  print "number of digits =", length(x)
  print substr(x, 1, 20), "...", substr(x, length(x) - 19, 20)
}

