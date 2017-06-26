#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
JK Utils Web.py Database Wrappers
Copyright (C) 2015-2017 Joxean Koret

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
02110-1301  USA
"""

import web
import random
import ConfigParser

#-------------------------------------------------------------------------------
def sqlite_concat(arg1, arg2):
  return str(arg1) + str(arg2)

#-------------------------------------------------------------------------------
def sqlite_conv(arg1, from_base, to_base):
  # We assume it's base 10
  return int(arg1, to_base)

#-------------------------------------------------------------------------------
def sqlite_instr(arg1, arg2):
  return str(arg1).find(arg2) + 1

#-------------------------------------------------------------------------------
def sqlite_rand():
  return random.random()

#-------------------------------------------------------------------------------
def get_dbn(cfg_file="config.cfg"):
  parser = ConfigParser.SafeConfigParser()
  parser.optionxform = str
  parser.read(cfg_file)

  section = 'database'
  if 'database' not in parser.sections():
    raise Exception("No database section in %s" % cfg_file)

  return parser.get(section, 'dbn')

#-------------------------------------------------------------------------------
def init_web_db(cfg_file="config.cfg"):
  parser = ConfigParser.SafeConfigParser()
  parser.optionxform = str
  parser.read(cfg_file)

  section = 'database'
  if 'database' not in parser.sections():
    raise Exception("No database section in %s" % cfg_file)

  dbn = parser.get(section, 'dbn')

  if dbn == "mysql":
    db = parser.get(section, 'db')
    user = parser.get(section, 'user')
    pw = parser.get(section, 'pw')
    host = parser.get(section, 'host')
    db = web.database(dbn='mysql', db=db, user=user, pw=pw, host=host)
    
    db.query('SET NAMES utf8;')
    db.query('SET CHARACTER SET utf8;')
    db.query('SET character_set_connection=utf8;')
  elif dbn == "sqlite":
    dbname = parser.get(section, 'db')
    db = web.database(dbn='sqlite', db=dbname)
    
    # We need to mimic some MySQL functions in order to be able to use
    # SQLite or use different SQL commands for each database server. I
    # prefer the 1st option, naturally...
    db._db_cursor().connection.create_function("concat", 2, sqlite_concat)
    db._db_cursor().connection.create_function("conv", 3, sqlite_conv)
    db._db_cursor().connection.create_function("instr", 2, sqlite_instr)
    db._db_cursor().connection.create_function("rand", 0, sqlite_rand)

  db._db_cursor().connection.text_factory = str

  return db

#-------------------------------------------------------------------------------
def webpy_connect_db():
  db = init_web_db()
  return db._db_cursor().connection

