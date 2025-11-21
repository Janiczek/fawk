BEGIN {
  # Test 1: Read multiple lines from a command
  cmd = "printf 'line1\\nline2\\nline3\\n'"
  cmd | getline result1
  cmd | getline result2
  cmd | getline result3
  close(cmd)
  print "Test 1: " result1 " " result2 " " result3
  
  # Test 2: Read without variable (into $0)
  cmd2 = "echo 'hello world'"
  cmd2 | getline
  close(cmd2)
  print "Test 2: " $0
  
  # Test 3: Close and reopen same command
  cmd3 = "echo 'first run'"
  cmd3 | getline run1
  close(cmd3)
  cmd3 | getline run2
  close(cmd3)
  print "Test 3: " run1 " | " run2
}
