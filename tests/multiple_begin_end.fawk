# Test: Multiple BEGIN and END blocks execute in order

BEGIN {
  print("BEGIN 1")
  x = 1
}

BEGIN {
  print("BEGIN 2")
  x = x + 1
}

BEGIN {
  print("BEGIN 3")
  x = x + 1
  print("x =", x)
}

END {
  print("END 1")
  y = 10
}

END {
  print("END 2")
  y = y + 10
}

END {
  print("END 3")
  y = y + 10
  print("y =", y)
}

