#!/usr/bin/python

import sys
import time
import sqlite3

from idc import *
from idaapi import *
from idautils import *

from jkutils.simple_log import log
from diaphora_ida import CIDABinDiff

#-------------------------------------------------------------------------------
BANNED_NAMES = ["start", "WinMain", "DllMain", "DllRegisterServer", 
  "DllUnregisterServer", "TopLevelExceptionFilter"]

#-------------------------------------------------------------------------------
class CIndexSymbolyzer:
  def __init__(self, db_name):
    self.diff = CIDABinDiff(db_name=":memory:")
    self.diff.use_decompiler_always = False

    self.db = sqlite3.connect(db_name)

  def __def__(self):
    if self.db is not None:
      self.db.close()
  
  def name_is_banned(self, name):
    return name in BANNED_NAMES

  def find_symbol_for(self, func_data):
    # Get each field from the list
    name, nodes, edges, indegree, outdegree, size, instructions, mnems, names,      \
    proto, cc, prime, f, comment, true_name, bytes_hash, pseudo, pseudo_lines,      \
    pseudo_hash1, pseudocode_primes, function_flags, asm, proto2,                   \
    pseudo_hash2, pseudo_hash3, strongly_connected_len, loops, rva, bb_topological, \
    strongly_connected_spp, clean_assembly, clean_pseudo, mnemonics_spp, switches,  \
    function_hash, bytes_sum, md_index, basic_blocks_data, bb_relations = func_data
    
    sql = """select distinct name, function_hash, bytes_hash, md_index,
                    pseudocode_primes
               from samples_data
              where name not like 'sub_%'
                and name not like 'nullsub%'
                and name not like 'SEH_%'
                and (function_hash = ?
                 or bytes_hash = ?
                 or (names = ?
                and md_index = ?
                and cast(md_index as real) > 0)
                 or (nodes = ? and edges = ? and outdegree = ? and loops = ?
                 and bb_topological = ? and strongly_connected_spp = ?
                 and cast(nodes as integer) >= 10))
                and cast(nodes as integer) > 7"""
    cur = self.db.cursor()
    cur.execute(sql, (function_hash, bytes_hash, str(names), md_index,
                      nodes, edges, outdegree, loops, bb_topological, \
                      str(strongly_connected_spp)))

    found = False
    names = {}
    for row in cur.fetchall():
      #log("Found row %s" % repr(row))
      #log("While finding symbol for %s at 0x%x" % (name, f))
      #log("Data is %s %s %s %s" % (function_hash, bytes_hash, md_index, pseudocode_primes))
      try:
        names[row[0]] += 1
      except KeyboardInterrupt:
        raise
      except:
        names[row[0]] = 1

      found = True
    
    if len(names) > 0:
      top = 0
      top_name = None
      multiple = False
      for key in names:
        if names[key] > top:
          top = names[key]
          top_name = key
        elif names[key] == top and top != 0:
          multiple = True

      others = []
      for key in names:
        if key != top_name:
          others.append("%s (%d matches)" % (key, names[key]))

      if multiple:
        log("Multiple matches for 0x%x (%d total)" % (f, len(names)))
        MakeComm(f, "MalIndex: Matches " + str(",\n".join(names.keys())))
      else:
        log("Found name %s for 0x%x (%d matches)" % (top_name, f, top))
        MakeNameEx(f, str(top_name), idc.SN_AUTO)
        if len(others) > 0:
          cmt = "MalIndex: Other possible matches %s" % ", ".join(others)
          MakeComm(f, str(cmt))

    cur.close()
    return found

  def has_no_name(self, name):
    if name.startswith("sub_"):
      return True
    
    # Ignore these functions
    if name.startswith("nullsub_") or name.startswith("SEH_"):
      return False

    return False

  def find_symbols_internal(self):
    i = 0
    t = time.time()
    funcs = list(Functions())
    total_funcs = len(funcs)
    for f in funcs:
      i += 1
      if (total_funcs > 100) and i % (total_funcs/100) == 0 or i == 1:
        line = "Searched %d function(s) out of %d total.\nElapsed %d:%02d:%02d second(s), remaining time ~%d:%02d:%02d"
        elapsed = time.time() - t
        remaining = (elapsed / i) * (total_funcs - i)

        m, s = divmod(remaining, 60)
        h, m = divmod(m, 60)
        m_elapsed, s_elapsed = divmod(elapsed, 60)
        h_elapsed, m_elapsed = divmod(m_elapsed, 60)

        replace_wait_box(line % (i, total_funcs, h_elapsed, m_elapsed, s_elapsed, h, m, s))

      name = GetFunctionName(f)
      if self.has_no_name(name):
        func_data = self.diff.read_function(f)
        if type(func_data) is not tuple:
          continue

        self.find_symbol_for(func_data)

  def find_symbols(self):
    try:
      show_wait_box("Exporting current database and finding symbols...")
      self.find_symbols_internal()
    finally:
      hide_wait_box()
      log("Done")

#-------------------------------------------------------------------------------
def main():
  db_name = "/home/joxean/Documentos/research/diaphora/indexes.sqlite"
  sym = CIndexSymbolyzer(db_name)
  sym.find_symbols()

if __name__ == "__main__":
  main()
