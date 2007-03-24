"""An incomplete clean room implementation of java.util.Properties written in Python.

Copyright (C) 2002,2004 - Ollie Rutherfurd <oliver@rutherfurd.net>

Unicode support added by Christopher Eppstein <chris@eppsteins.net>

Based on:

  http://java.sun.com/j2se/1.3/docs/api/java/util/Properties.html

License: Python License

Example Usage:

>>> from properties import Properties
>>> props = Properties()
>>> props['one'] = '1'
>>> props['your name'] = "I don't know"
>>> print '\n'.join(props.keys())
your name
one
>>> from StringIO import StringIO
>>> buff = StringIO()
>>> props.store(buff, "a little example...")
>>> buff.seek(0)
>>> print buff.read()
# a little example...
your\ name=I\ don\'t\ know
one=1
>>> print props['your name']
I don't know

$Id: properties.py,v 1.2 2002/04/21 02:52:53 oliver Exp $

"""

__all__ = ['Properties']


def escapestr(s):
  buff = []
  # QUESTION: escape leading or trailing spaces?
  for c in s:
    if c == '\\':
      buff.append('\\\\')
    elif c == '\t':
      buff.append('\\t')
    elif c == '\n':
      buff.append('\\n')
    elif c == '\r':
      buff.append('\\r')
    elif c == ' ':
      buff.append('\\ ')
    elif c == "'":
      buff.append("\\'")
    elif c == '"':
      buff.append('\\"')
    elif c == '#':
      buff.append('\\#')
    elif c == '!':
      buff.append('\\!')
    elif c == '=':
      buff.append('\\=')
    else:
      buff.append(c.encode("unicode_escape"))

  return ''.join(buff)


def unescapestr(line):

  buff = []
  escape = 0
  skip = 0
  for i in range(len(line)):
    if skip > 0:
      skip -= 1
      continue
    c = line[i]
    if c == '\\':
      if escape:
        escape = 0
        buff.append('\\')
        continue
      else:
        # this is to deal with '\'
        # acting as a line continuation
        # character
        if i == len(line) - 1:
          buff.append('\\')
          break
        else:
          escape = 1
          continue
    elif c == 'n':
      if escape:
        escape = 0
        buff.append('\n')
        continue
    elif c == 'r':
      if escape:
        escape = 0
        buff.append('\r')
        continue
    elif c == 't':
      if escape:
        escape = 0
        buff.append('\t')
        continue
    elif c == 'u':
      if escape:
        uchar = "\\u"+line[i+1:i+5]
        try:
          uchar = uchar.decode("unicode_escape")
          buff.append(uchar)
          skip = 4
          escape = 0
          continue
        except UnicodeDecodeError:
          escape = 0
          buff.append('u')
          continue
    buff.append(c)

    # make sure escape doesn't stay one
    # all expected escape sequences either break
    # or continue, so this should be safe
    if escape:
      escape = 0

  return ''.join(buff)



class Properties(dict):

  """
  Property class based on java.util.Properties.
  """

  def __init__(self, defaults={}):
    dict.__init__(self)
    for n,v in defaults.items():
      self[n] = v

  def __getitem__(self,key):
    try:
      return dict.__getitem__(self,key)
    except KeyError:
      return None

  def read(self,filename):
    """
    Reads properties from a file (java Property class 
    reads from an input stream -- see load()).
    """
    f = None
    try:
      f = open(filename)
      self.load(f)
    finally:
      if f:
        f.close()

  def save(self,filename,header=None):
    """
    Save properties to a file.
    """
    f = None
    try:
      f = open(filename,"w")
      self.store(f,header)
    finally:
      if f:
        f.close()

  def load(self, buff):
    """
    Reads properties from a stream (StringIO, file, etc...)
    """
    props = readprops(buff)
    for n,v in props.iteritems():
      self[n] = v

  def store(self, buff, header=None):
    """
    Saves properties to a stream (StringIO, file, etc...)
    """
    if header:
      print >> buff, '#', header.encode("utf-8")
    for n,v in self.iteritems():
      print >> buff, '%s=%s' % (escapestr(n),escapestr(v),)


def readprops(buff):

  name,value = None,''
  props = {}
  continued = 0

  while 1:
    line = buff.readline()
    if not line:
      break
    line = line.strip()

    # empty line
    if not line:
      continue

    # comment
    if line[0] in ('#','!'):
      continue

    # find name
    i,escaped = 0,0
    while i < len(line):
      c = line[i]

      if c == '\\':
        if escaped:
          escaped = 0
        else:
          escaped = 1
        i += 1
        continue

      elif c in (' ', '\t', ':', '=') and not escaped:
        name = unescapestr(line[:i])
        break

      # make sure escaped doesn't stay on
      if escaped:
        escaped = 0

      i += 1

    # no dlimiter was found, name is entire line, there is no value
    if name == None:
      name = unescapestr(line.lstrip())

    # skip delimiter
    while line[i:i+1] in ('\t', ' ', ':', '='):
      i += 1

    value = unescapestr(line[i:].strip())
    while value[-1:] == '\\':
      value = value[:-1]  # remove \
      line = buff.readline()
      if not line:
        break
      value += unescapestr(line.strip())

    #print 'value:',value ##
    props[name] = value

  return props
# :indentSize=2:lineSeparator=\n:noTabs=true:tabSize=2:
