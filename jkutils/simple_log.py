#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
JK Utils Simple Logging Library
Copyright (c) 2015-2017 Joxean Koret

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

import os
import sys
import time
import thread

DEBUG = False

#-----------------------------------------------------------------------
def log(msg):
  print "[%s %d:%d] %s" % (time.asctime(), os.getpid(), thread.get_ident(), msg)
  sys.stdout.flush()

#-----------------------------------------------------------------------
def debug(msg):
  global DEBUG

  if DEBUG:
    log(msg)
