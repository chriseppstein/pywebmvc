#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

"""Utilties for working with forms."""

import urllib
from parser import getPyWebMvcConfig

def href(request, globalForwardId, data = None):
  """utility function to construct a (server-relative) URL from a global
  forward id. C{data} can be a list of C{(name, value)} tuples or a dict of
  C{name -> value} mappings."""
  url = getPyWebMvcConfig(request).globalForwards[globalForwardId].getUrl()
  if data:
    query = "?"+urllib.urlencode(data)
  else:
    query = ""
  return url+query
