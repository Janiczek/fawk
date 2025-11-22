# Test: Multiple BEGINFILE and ENDFILE blocks execute in order

BEGINFILE {
  print("BEGINFILE 1 for", FILENAME)
  file_x = 1
}

BEGINFILE {
  print("BEGINFILE 2 for", FILENAME)
  file_x = file_x + 1
}

BEGINFILE {
  print("BEGINFILE 3 for", FILENAME)
  file_x = file_x + 1
  print("file_x =", file_x)
}

{
  print($0)
}

ENDFILE {
  print("ENDFILE 1 for", FILENAME)
  file_y = 10
}

ENDFILE {
  print("ENDFILE 2 for", FILENAME)
  file_y = file_y + 10
}

ENDFILE {
  print("ENDFILE 3 for", FILENAME)
  file_y = file_y + 10
  print("file_y =", file_y)
}

