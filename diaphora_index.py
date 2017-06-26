#!/usr/bin/python

import os
import json
import time
import idaapi

from diaphora_ida import CIDABinDiff

from jkutils.simple_log import log
from jkutils.web_db import init_web_db

#-------------------------------------------------------------------------------
class CBinaryIndexer:
  def __init__(self, cfg_file):
    self.diff = CIDABinDiff(db_name=":memory:")
    self.diff.use_decompiler_always = True

    self.db = init_web_db(cfg_file)
    self.db.printing = False
    self.db.text_factory = str
    self.create_schema()

    self.md5 = None
    self.path = None

  def __def__(self):
    if self.db is not None:
      self.db.close()

  def create_schema(self):
    sql = """create table if not exists samples_data (
                id integer not null primary key autoincrement,
                name, nodes, edges, indegree, outdegree, size, instructions, mnems, names,
                proto, cc, prime, address, comment, true_name, bytes_hash, pseudo, pseudo_lines,
                pseudo_hash1, pseudocode_primes, function_flags, asm, proto2,
                pseudo_hash2, pseudo_hash3, strongly_connected_len, loops, rva, bb_topological,
                strongly_connected_spp, clean_assembly, clean_pseudo, mnemonics_spp, switches,
                function_hash, bytes_sum, md_index, basic_blocks_data, bb_relations,
                md5, file_name)"""
    self.db.query(sql)

    sql = "create unique index if not exists uq_samples_data on samples_data(md5, address)"
    self.db.query(sql)

    sql = """create table if not exists samples (
                id integer not null primary key autoincrement,
                md5, file_name, date) """
    self.db.query(sql)

  def save_data(self, data):
    # Convert to a list with the proper data type for each colum
    list_data = []
    for prop in list(data):
      if type(prop) is long and prop > 0xFFFFFFFF:
        prop = str(prop)

      if type(prop) is list or type(prop) is set or type(prop) is dict:
        list_data.append(json.dumps(list(prop)))
      else:
        list_data.append(str(prop))

    # Get each field from the list
    name, nodes, edges, indegree, outdegree, size, instructions, mnems, names,      \
    proto, cc, prime, f, comment, true_name, bytes_hash, pseudo, pseudo_lines,      \
    pseudo_hash1, pseudocode_primes, function_flags, asm, proto2,                   \
    pseudo_hash2, pseudo_hash3, strongly_connected_len, loops, rva, bb_topological, \
    strongly_connected_spp, clean_assembly, clean_pseudo, mnemonics_spp, switches,  \
    function_hash, bytes_sum, md_index, basic_blocks_data, bb_relations = list_data

    # And finally insert the data
    seq_id = self.db.insert("samples_data", name=name, nodes=nodes, edges=edges,
                      indegree=indegree, outdegree=outdegree, size=size,
                      instructions=instructions, mnems=mnems, names=names,
                      proto=proto, cc=cc, prime=prime, address=f, 
                      true_name=true_name, bytes_hash=bytes_hash,
                      pseudo=pseudo, pseudo_lines=pseudo_lines,
                      pseudo_hash1=pseudo_hash1, pseudocode_primes=pseudocode_primes,
                      function_flags=function_flags, asm=asm, proto2=proto2,
                      pseudo_hash2=pseudo_hash2, pseudo_hash3=pseudo_hash3,
                      strongly_connected_len=strongly_connected_len,
                      loops=loops, rva=rva, bb_topological=bb_topological,
                      strongly_connected_spp=strongly_connected_spp,
                      clean_assembly=clean_assembly, clean_pseudo=clean_pseudo,
                      mnemonics_spp=mnemonics_spp, switches=switches,
                      function_hash=function_hash, bytes_sum=bytes_sum,
                      md_index=md_index, basic_blocks_data=basic_blocks_data,
                      bb_relations=bb_relations, md5=self.md5, file_name=self.path)

  def update_stats(self):
    sql = "drop table if exists unique_md_indexes"
    self.db.query(sql)

    sql = "drop index if exists idx_unique_md_indexes"
    self.db.query(sql)

    sql = """ create table unique_md_indexes
                  as
              select distinct md_index md_index, count(*) total, (count(*) * 100.00) / (select count(distinct md_index) from samples_data) percent
                from samples_data
               where md_index != '0'
               group by md_index
               having (count(*) * 100.00) / (select count(distinct md_index) from samples_data) < 0.003"""
    self.db.query(sql)

    sql = "create index idx_unique_md_indexes on unique_md_indexes(md_index)"
    self.db.query(sql)

    sql = "drop table if exists unique_function_hashes"
    self.db.query(sql)
    
    sql = "drop index if exists idx_unique_function_hashes"
    self.db.query(sql)

    sql = """ create table unique_function_hashes
              as
              select distinct function_hash function_hash, count(*) total, (count(*) * 100.00) / (select count(distinct function_hash) from samples_data) percent
              from samples_data
              where function_hash != '0' and function_hash is not null
              group by function_hash
              having (count(*) * 100.00) / (select count(distinct function_hash) from samples_data) < 0.003"""
    self.db.query(sql)
    
    sql = "create index idx_unique_function_hashes on unique_function_hashes(function_hash)"
    self.db.query(sql)

  def save_sample(self):
    self.db.insert("samples", md5=self.md5, file_name=self.path, date=time.asctime())

  def is_file_indexed(self, md5, path):
    db_vars = {"md5":md5, "file_name":path}
    results = self.db.select('samples', db_vars, where="md5 = $md5 and file_name = $file_name")
    rows = list(results)
    return len(rows) != 0

  def index(self):
    self.md5 = GetInputFileMD5()
    self.path = GetIdbPath()

    if self.is_file_indexed(self.md5, self.path):
      log("File with MD5 %s at %s already indexed" % (self.md5, self.path))
      return

    log("Starting the indexing process...")
    for f in Functions():
      func_data = self.diff.read_function(f)
      if type(func_data) is not tuple:
        continue

      try:
        self.save_data(func_data)
      except:
        break

    self.save_sample()
    self.update_stats()
    log("Done!")

if __name__ == "__main__":
  idaapi.autoWait()

  cfg_file = os.getenv("DIAPHORA_DB_CONFIG")
  if cfg_file is None:
    cfg_file = "/home/joxean/Documentos/research/diaphora/diaphora_idx.cfg"

  try:
    indexer = CBinaryIndexer(cfg_file)
    indexer.index()

    idaapi.qexit(0)
  except:
    print "Error:", sys.exc_info()[1]
    raise

