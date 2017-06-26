#!/usr/bin/python

import os
import sys
import shlex
import sqlite3
import webbrowser

try:
  import readline
  import atexit

  histfile = os.path.join(os.path.expanduser("~"), ".mal_index")

  try:
    readline.read_history_file(histfile)
    # default history len is -1 (infinite), which may grow unruly
    readline.set_history_length(1000)
  except IOError:
    pass

  atexit.register(readline.write_history_file, histfile)
except:
  pass

from terminal import get_terminal_size

#-------------------------------------------------------------------------------
class CMalIndex:
  def __init__(self, db_name):
    self.db_name = db_name
    self.db = sqlite3.connect(db_name)

  def get_samples(self, arg):
    sql = "select md5, file_name, date from samples"
    if arg is not None:
      sql += " where md5 like ? or file_name like ? or date like ?"
    else:
      sql += " where (? is null or ? is null or ? is null) "
    sql += " order by id desc"

    cur = self.db.cursor()
    cur.execute(sql, (arg, arg, arg, ))
    return cur

  def get_unique_matches(self, md5_hash):
    sql = """ select case
                     when sd1.function_hash = sd2.function_hash then
                       "F"
                     when sd1.bytes_hash = sd2.bytes_hash then
                       "B"
                     when sd1.md_index = sd2.md_index then
                       "M"
                     when sd1.pseudocode_primes = sd2.pseudocode_primes then
                       "S"
                     else
                       "I"
                     end "Type",
                     sd1.name "Name 1", sd2.md5 "MD5", sd2.name "Name 2", 
                     case
                     when sd1.function_hash = sd2.function_hash then
                       sd1.function_hash
                     when sd1.bytes_hash = sd2.bytes_hash then
                       sd1.bytes_hash
                     when sd1.md_index = sd2.md_index then
                       sd1.md_index
                     when sd1.pseudocode_primes = sd2.pseudocode_primes then
                       sd1.pseudocode_primes
                     else
                       sd1.mnems
                     end "Hash",
                     sd2.file_name "Filename"
                from samples_data sd1,
                     samples_data sd2
               where sd1.md5 != sd2.md5
                 and ((sd1.function_hash = sd2.function_hash
                 and sd1.function_hash in (select function_hash from unique_function_hashes where total <= 2))
                  or (sd1.bytes_hash = sd2.bytes_hash
                 and (select count(*) from samples_data where function_hash = sd1.function_hash) <= 2)
                  or (sd1.md_index = sd2.md_index
                 and sd2.md_index in (select md_index from unique_md_indexes where total <= 2))
                  or (sd1.mnems = sd2.mnems and sd1.instructions > 30
                 and (select count(*) from samples_data where mnems = sd1.mnems) <= 2))
                 and cast(sd1.nodes as integer) > 7
                 and cast(sd2.nodes as integer) > 7
                 and sd1.function_hash is not null
                 and sd2.function_hash is not null
                 and sd1.md5 = ?"""
    cur = self.db.cursor()
    cur.execute(sql, (md5_hash,))
    return cur

  def get_matching_samples(self, md5_hash, md5_hash2 = None):
    sql = """ select case
                     when sd1.function_hash = sd2.function_hash then
                       "F"
                     when sd1.bytes_hash = sd2.bytes_hash then
                       "B"
                     when sd1.md_index = sd2.md_index then
                       "M"
                     when sd1.pseudocode_primes = sd2.pseudocode_primes then
                       "S"
                     else
                       "I"
                     end "Type",
                     sd1.name "Name 1", sd2.md5 "MD5", sd2.name "Name 2", 
                     case
                     when sd1.function_hash = sd2.function_hash then
                       sd1.function_hash
                     when sd1.bytes_hash = sd2.bytes_hash then
                       sd1.bytes_hash
                     when sd1.md_index = sd2.md_index then
                       sd1.md_index
                     when sd1.pseudocode_primes = sd2.pseudocode_primes then
                       sd1.pseudocode_primes
                     else
                       sd1.mnems
                     end "Hash",
                     sd2.file_name "Filename"
                from samples_data sd1,
                     samples_data sd2
               where sd1.md5 != sd2.md5
                 and ((sd1.function_hash = sd2.function_hash
                  and sd1.function_hash in (select function_hash from unique_function_hashes))
                   or sd1.bytes_hash = sd2.bytes_hash
                   or (sd1.md_index = sd2.md_index
                   and sd2.md_index in (select md_index from unique_md_indexes))
                   or (sd1.mnems = sd2.mnems and sd1.instructions > 30))
                 and cast(sd1.nodes as integer) > 7
                 and cast(sd2.nodes as integer) > 7
                 and sd1.function_hash is not null
                 and sd2.function_hash is not null"""
    cur = self.db.cursor()

    if md5_hash2 is None:
      sql += " and sd1.md5 = ?"
      cur.execute(sql, (md5_hash,))
    else:
      sql += " and sd1.md5 in (?, ?) and sd2.md5 in (?, ?)"
      cur.execute(sql, (md5_hash, md5_hash2, md5_hash, md5_hash2))
    return cur

  def get_samples_by(self, method, hash_value):
    if method in ["function", "fhash"]:
      column = "function_hash"
    elif method in ["bytes", "bhash"]:
      column = "bytes_hash"
    elif method in ["md", "mdindex"]:
      column = "md_index"
    else:
      raise Exception("Unknown method used!")

    sql = "select md5, name, file_name from samples_data where %s = ? and %s is not null"
    sql %= (column, column)
    cur = self.db.cursor()
    cur.execute(sql, (hash_value,))
    return cur
  
  def find_function_name(self, hash_value):
    sql = """select distinct name "Function Name", file_name "Filename"
               from samples_data
              where (function_hash = ?
                 or bytes_hash = ?
                 or md_index = ?)
                and name not like 'sub_%'"""
    cur = self.db.cursor()
    cur.execute(sql, (hash_value, hash_value, hash_value))
    return cur
  
  def find_samples_by_function(self, function_name):
    sql = "select md5, name, file_name from samples_data where name like ?"
    cur = self.db.cursor()
    cur.execute(sql, (function_name,))
    return cur

#-------------------------------------------------------------------------------
def show_help():
  print "Help:"
  print
  print "samples %expression%           List samples matching expression"
  print "match md5 [md5]                Show samples matching a specific MD5 or matches between 2 samples"
  print "function hash                  Show samples matching a specific function hash"
  print "bytes hash                     Show samples matching a specific bytes hash"
  print "mdindex hash                   Show samples matching a specific MD Index"
  print "report/vt hash                 Show the VirusTotal report for the given hash"
  print "name hash                      Find function names for the given function/bytes/mdindex hash"
  print "fname hash                     Find samples with the given function name"
  print "exec cmd                       Execute an operating system command"
  print "q/quit/exit                    Exit from the application"
  print "help/?                         Show this help"

#-------------------------------------------------------------------------------
def show_results(cur):
  # Print header
  cols, rows = get_terminal_size()
  columns = []
  for desc in cur.description:
    columns.append(desc[0])
  line = " | ".join(columns)
  print line
  print "-" * len(line)

  # Print lines
  try:
    i = 0
    total = 0
    cnt = cur.rowcount
    while 1:
      line = cur.fetchone()
      if not line:
        break
      total += 1

      print " ".join(line)
      i += 1
      if i == rows - 3 and i > cnt:
        i = -2
        try:
          cmd = raw_input("--- Enter to continue, 'q' to quit --- ")
        except KeyboardInterrupt:
          print
          break

        if cmd == "q":
          break
    print("Total of %s" % (total == 1 and "1 row." or "%d rows." % total))
  finally:
    cur.close()

#-------------------------------------------------------------------------------
def main(args):
  db_name = args[0]
  mal_index = CMalIndex(db_name)

  while 1:
    try:
      line = raw_input("MalIndex> ")
    except KeyboardInterrupt:
      print
      break

    tokens = shlex.split(line)
    if len(tokens) == 0:
      continue

    try:
      run_command(mal_index, tokens)
    except SystemExit:
      break
    except:
      print "Error: %s" % str(sys.exc_info()[1])

#-------------------------------------------------------------------------------
def run_command(mal_index, tokens):
  cmd = tokens[0]
  cmd_args = tokens[1:]
  if cmd in ["quit", "exit", "q"]:
    sys.exit(0)
  elif cmd in ["help", "?"]:
    show_help()
  elif cmd in ["samples"]:
    arg = None
    if len(cmd_args) > 0:
      arg = "%" + cmd_args[0] + "%"
    cur = mal_index.get_samples(arg)
    show_results(cur)
  elif cmd in ["match"]:
    if len(cmd_args) == 0:
      print "Usage: match <md5 of sample1> <md5 of sample2>"
      return

    md5_hash = cmd_args[0]
    md5_hash2 = None
    if len(cmd_args) > 1:
      md5_hash2 = cmd_args[1]
      print "Searching for matches between %s and %s..." % (md5_hash, md5_hash2)
    else:
      print "Searching for %s..." % md5_hash
    cur = mal_index.get_matching_samples(md5_hash, md5_hash2)
    show_results(cur)
  elif cmd in ["unique"]:
    if len(cmd_args) == 0:
      print "Usage: unique <md5>"
      return

    md5_hash = cmd_args[0]
    print "Searching unique matches for %s..." % md5_hash
    cur = mal_index.get_unique_matches(md5_hash)
    show_results(cur)
  elif cmd in ["exec", "!"]:
    os.system(" ".join(cmd_args))
  elif cmd in ["fhash", "function", "bhash", "bytes", "md", "mdindex"]:
    if len(cmd_args) == 0:
      print "Usage: %s <hash>" % cmd
      return

    fhash = cmd_args[0]
    cur = mal_index.get_samples_by(cmd, fhash)
    show_results(cur)
  elif cmd in ["vt", "report"]:
    if len(cmd_args) == 0:
      print "Usage: %s <cryptographic hash>" % cmd
      return

    url = "http://www.virustotal.com/search?query=%s" % cmd_args[0]
    webbrowser.open(url)
  elif cmd in ["name"]:
    if len(cmd_args) == 0:
      print "Usage: %s <any hash>"
      return

    cur = mal_index.find_function_name(cmd_args[0])
    show_results(cur)
  elif cmd in ["fname"]:
    if len(cmd_args) == 0:
      print "Usage: %s <function name>"
      return

    cur = mal_index.find_samples_by_function(cmd_args[0])
    show_results(cur)
  else:
    print "Unknown command %s" % repr(cmd)

#-------------------------------------------------------------------------------
def usage():
  print "Usage:", sys.argv[0], "<sqlite database> [options]"

if __name__ == "__main__":
  if len(sys.argv) == 1:
    usage()
  else:
    main(sys.argv[1:])
