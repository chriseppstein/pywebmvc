#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""Associate a L{properties} file to a Locale.
"""

import re, types, sys
from util import PyWebMvcObject
from properties import Properties

class ResourceBundle(PyWebMvcObject):
  """Extends a L{Properties<properties.Properties>} file to allow for
  parameterized substitution and property references (terms). Parameters are in
  the form C{{N}} where N is an zero-based index of the paramters to the
  getMessage function. Terms take the form C{${resourcekey}} and allow a
  resource entry to refer to another resource entry. It is not recommended that
  you place parameters in your terms, but it is allowed since parameter
  substitution is performed after term expansion. Example::

    term.foo=Foo
    term.idea=idea
    term.modifiedIdea={1} ${term.idea}
    message.bar=This is my {0} ${term.foo}.
    message.badIdea=This is a {0} ${term.modifiedIdea}.
    message.fineIdea=This is a {0} {1}.
    message.goodIdea=This is a {0} {1} ${term.idea}.

  >>> bundle["term.foo"]
  'Foo'
  >>> bundle["term.modifiedIdea"]
  '{1} idea'
  >>> bundle.getMessage("message.bar","Silly")
  'This is my Silly Foo.'
  >>> bundle.getMessage("message.badIdea","really", "bad")
  'This is a really bad idea.'
  >>> bundle.getMessage("message.fineIdea","perfectly",
  ...                   bundle.getMessage("term.modifiedIdea","fine"))
  'This is a perfectly fine idea.'
  >>> bundle.getMessage("message.goodIdea","much", "better")
  'This is a much better idea.'
  """
  def __init__(self, propertiesFile = None):
    self.props = Properties()
    if propertiesFile:
      self.addPropertiesFile(propertiesFile)
  def addPropertiesFile(self, propertiesFile):
    if isinstance(propertiesFile, types.StringTypes):
      self.props.read(propertiesFile)
    else:
      self.props.load(propertiesFile)
    self.resolve_terms()
  def addPropertiesFiles(self, propertiesFiles):
    for f in propertiesFiles:
      self.addPropertiesFile(f)
  def resolve_terms(self):
    for key in self.props.keys():
      self.props[key] = self.replaceTerms(self.props[key])
  def has_term(self,msg):
    idx = msg.find("${")
    if idx < 0:
      return False
    else:
      return msg.find("}",idx) >= 0
  def get_term(self,msg,all=False):
    tokens = re.split("(\\$\\{|\\})",msg)
    startCount = 0
    term = ""
    terms = []
    for token in tokens:
      if token == "${":
        startCount += 1
        if startCount > 1:
          term += token
      elif token == "}" and startCount > 0:
        startCount -= 1
        if startCount == 0:
          if all:
            terms.append(term)
            term = ""
          else:
            return term
        else:
          term += token
      elif startCount > 0:
        term += token
    if startCount > 0:
      raise ValueError("Malformed term found in message resource: "+msg)
    if all:
      return terms
    else:
      return None
  def replaceTerms(self, msg, paramMap = {}):
    terms = self.get_term(msg,all=True)
    for term in terms:
      origTerm = term
      try:
        if self.has_term(term):
          term = self.replaceTerms(term, paramMap)
        if paramMap.has_key(term):
          termVal = paramMap[term]
        else:
          termVal = self.getMessage(term,paramMap)
        msg = msg.replace("${"+origTerm+"}",termVal)
      except KeyError:
        pass
    return msg
  def keys(self):
    return self.props.keys()
  def has_key(self, key):
    return self.props.has_key(key)
  def getItemWithMap(self, key, map = {}):
    if self.props.has_key(key):
      return self.replaceTerms(self.props[key],map)
    else:
      raise KeyError(key)
  def __getitem__(self, key):
    return self.getItemWithMap(key)
  def __setitem__(self, key, value):
    self.props[key] = value

  def getMessageWithMap(self, key, paramList, paramMap):
    msg = self.getItemWithMap(key, paramMap)
    msg = self.substituteParams(msg, paramList)
    return msg

  def getMessage(self, key, *args, **kwargs):
    return self.getMessageWithMap(key, args, kwargs)

  def substituteParams(self, msg, args):
    result = msg
    i = 0
    for arg in args:
      parameter = ("{%i}" % (i))
      argStr = unicode(arg)
      result = result.replace(parameter, argStr)
      i = i + 1
    return result


  def getItemArrayWithMap(self, key, messageParams, paramMap):
    arrayResult = []
    count = 0
    while(True):
      #str:ok
      arrayKey = key + "." + str(count)
      if(not self.props.has_key(arrayKey)): break
      item = self.replaceTerms(self.props[arrayKey], paramMap)
      item = self.substituteParams(item, messageParams)
      arrayResult.append(item)
      count += 1
    return arrayResult

  def getItemArray(self, key, *messageParams, **kwargs):
    return self.getItemArrayWithMap(key, messageParams, kwargs)
  
class BundleManager(PyWebMvcObject):
  def __init__(self):
    self.defaultLocale = None
    self.bundles = {}
  def registerBundle(self, language, bundle):
    assert isinstance(bundle,ResourceBundle)
    self.bundles[language] = bundle
  def setDefaultLocale(self,locale):
    if locale is None:
      self.defaultLocale = None
    else:
      assert locale in self.bundles.keys()
      self.defaultLocale = locale
  def supportsLocale(self, locale):
    return self.bundles.has_key(locale)
  def negotiateLocale(self, preferedLanguages):
    for lang in preferedLanguages:
      if self.supportsLocale(lang):
        return lang
    return self.defaultLocale
  def getBundle(self, locale):
    if (locale is None) and (self.defaultLocale):
      return self.bundles[self.defaultLocale]
    elif locale:
      return self.bundles[locale]
    else:
      return {}

if __name__ == "__main__":
  bundle = ResourceBundle(sys.argv[1])
  for key in bundle.props.keys():
    print "%s=%s" % (key, bundle.props[key])
