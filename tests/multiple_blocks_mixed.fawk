# Test: Multiple blocks of all types mixed together

BEGIN {
  print("BEGIN A")
}

BEGINFILE {
  print("BEGINFILE A")
}

BEGIN {
  print("BEGIN B")
}

ENDFILE {
  print("ENDFILE A")
}

END {
  print("END A")
}

BEGINFILE {
  print("BEGINFILE B")
}

ENDFILE {
  print("ENDFILE B")
}

END {
  print("END B")
}

{
  print("Pattern:", $0)
}

