function hash_file(filename) {
  cmd = "md5sum --quiet " filename
  cmd | getline hash
  close(cmd)
  return hash
}

function hash_str(str) {
  filename = "/tmp/to_hash.txt"
  printf("%s", str) >filename
  close(filename)
  return hash_file(filename)
}

BEGIN {
  print "\"\" -> " hash_str("")
  print "\"abc\" -> " hash_str("abc")
}

