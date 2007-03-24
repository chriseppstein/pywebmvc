#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

"""Utilities for working with HTML."""

import urllib
from types import ListType

def escapeAttribute(attr):
  """escape text meant to be used within an html tag attribute."""
  #TODO: remove this unicode() when rendering separates metadata from attributes
  return unicode(attr).replace('"', '&quot;')
def escapeHtml(html):
  """escape text meant to be used between two html tags."""
  return html.replace('&','&amp;').replace('<', '&lt;').replace('>', '&gt;')
def escapeUrl(url):
  """escape text meant to be used within a url query string."""
  return urllib.quote_plus(url)
def truncateText(html, size):
  """If the C{html} is longer than C{size}, truncate it and have the truncated
  text become a hyperlink that, when clicked, displays the full text."""
  if len(html) > size:
    return '<a href="" onclick="alert(this.firstChild.firstChild.nodeValue); return false;"><span style="display: none;">%s</span>%s...</a>' % (escapeHtml(html),escapeHtml(html[0:size]))
  else:
    return html

def mapToListOfTuples(map):
  l = []
  for key in map.keys():
    value = map[key]
    if isinstance(value,ListType):
      for subvalue in value:
        l.append((key,subvalue))
    else:
      l.append((key, value))
  return l

def getParameterString(params):
  """Creates a url query string from a list of tuples or a dictionary::

  [(name, value), ...] or { name : value, name : [value1, value2, ...], ... }"""
  paramStr = ""
  if hasattr(params, "keys"):
    params = mapToListOfTuples(params)
  first = True
  for (key, value) in params:
    if first:
      first = False
    else:
      paramStr += "&"
    paramStr += escapeUrl(key)
    paramStr += "="
    paramStr += escapeUrl(value)
  return paramStr
