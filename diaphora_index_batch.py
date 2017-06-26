#!/usr/bin/python

import os
import sys
import magic

from hashlib import md5

from jkutils.web_db import init_web_db
from jkutils.simple_log import log, debug

#-------------------------------------------------------------------------------
def is_executable(magic_str):
  if magic_str.find("ASCII") > -1:
    return False

  return magic_str.lower().find("executable") > -1 \
      or magic_str.lower().find("shared object") > -1

#-------------------------------------------------------------------------------
def is_64bits(magic_str):
  magic_str = magic_str.lower()
  return magic_str.find("64") > -1 \
      or magic_str.find("PA-RISC2.0") > -1

#-------------------------------------------------------------------------------
class CBatchRunner:
  def __init__(self, ida_path, cfg_file):
    self.ida_path = ida_path
    self.diaphora_path = os.path.abspath(os.path.dirname(__file__))
    self.is_posix = os.name == "posix"

    self.db = init_web_db(cfg_file)
    self.db.printing = False
    self.db.text_factory = str

  def is_file_indexed(self, md5_hash):
    db_vars = {"md5":md5_hash.lower()}
    results = self.db.select('samples', db_vars, where="lower(md5) = $md5", limit=1)
    rows = list(results)
    return len(rows) != 0

  def do_run(self, filename, file_type):
    cmd = os.path.join(self.ida_path, "idaq")
    if is_64bits(file_type):
      cmd += "64"

    if filename.find(" ") > -1:
      filename = '"' + filename + '"'

    cmd_line = " ".join([cmd, "-A", "-B", "-S%s/diaphora_index.py" % self.diaphora_path, filename])
    if self.is_posix:
      cmd_line += " 2>/dev/null"

    log("Indexing %s" % filename)
    debug("Running %s" % cmd_line)
    os.system(cmd_line)

  def run(self, directory):
    for root, dirs, files in os.walk(directory, followlinks=True):
      for name in files:
        filename = os.path.join(root, name)
        try:
          file_type = magic.from_buffer(open(filename).read(1024))
        except:
          log("Error reading file %s: %s" % (filename, str(sys.exc_info()[1])))
          continue

        if is_executable(file_type):
          md5_hash = md5(open(filename, "rb").read()).hexdigest()
          if not self.is_file_indexed(md5_hash):
            self.do_run(filename, file_type)
          else:
            log("File already indexed %s" % name)

#-------------------------------------------------------------------------------
def usage():
  print "Usage:", sys.argv[0], "<ida directory> <directory>"

#-------------------------------------------------------------------------------
def main(ida_path, path):
  cfg_file = os.getenv("DIAPHORA_DB_CONFIG")
  if cfg_file is None:
    cfg_file = "/home/joxean/Documentos/research/diaphora/diaphora_idx.cfg"

  batch = CBatchRunner(ida_path, cfg_file = cfg_file)
  batch.run(path)

if __name__ == "__main__":
  if len(sys.argv) != 3:
    usage()
  else:
    main(sys.argv[1], sys.argv[2])
