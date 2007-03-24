from pywebmvc.framework.util import PyWebMvcObject
from types import StringTypes

def sqlstrescape(aStr):
  aStr = aStr.replace("\\","\\\\")
  aStr = aStr.replace("'","\\'")
  aStr = aStr.replace("\"","\\\"")
  return aStr

class SearchCriteria(PyWebMvcObject):
  def accepts(self, obj):
    """tests the python object to see if it meets the search criteria"""
  def __str__(self):
    """returns an SQL fragment for performing the search"""
    raise NotYetImplemented()

class BasicSearchCriteria(SearchCriteria):
  OP_EQUAL = "="
  OP_NOT_EQUAL = "<>"
  OP_LESS_THAN = "<"
  OP_GREATER_THAN = ">"
  OP_LESS_THAN_OR_EQUAL = "<="
  OP_GREATER_THAN_OR_EQUAL = ">="
  OP_LIKE = "like"
  def __init__(self, property, operator, value):
    self.property = property
    self.operator = operator
    self.value = value
  def accepts(self, obj):
    pyOp = self.operator
    if pyOp == BasicSearchCriteria.OP_EQUAL:
      pyOp = "=="
    if pyOp == self.OP_NOT_EQUAL:
      pyOp = "!="
    if pyOp == self.OP_LIKE:
      toEval = "unicode(obj.%s).lower().find(%s) != -1" % (self.property, repr(unicode(self.value.replace("%", "")).lower()))
    else:
      toEval = "unicode(obj.%s) %s %s" % (self.property, pyOp, repr(unicode(self.value)))
    return eval(toEval)
  def sql(self,columnMap):
    value = self.value
    if isinstance(value,StringTypes):
      value = "'%s'" % sqlstrescape(value.encode("utf-8"))
    else:
      value = repr(value)
    return "(%s %s %s)" % (columnMap[self.property], self.operator, value)


class InSearchCriteria(SearchCriteria):
  def __init__(self, property, valueList):
    self.property = property
    self.valueList = valueList
  def accepts(self, obj):
    return True
  def sql(self,columnMap):
    return "(%s in (%s))" % (columnMap[self.property], ",".join(map(lambda x: isinstance(x, StringTypes) and "'%s'" % (sqlstrescape(x)) or repr(x), self.valueList)))


class AndSearchCriteria(SearchCriteria):
  SQL_AND = "AND"
  def __init__(self, criteria1, criteria2):
    self.criteria1 = criteria1
    self.criteria2 = criteria2
  def accepts(self, obj):
    return self.criteria1.accepts(obj) and self.criteria2.accepts(obj)
  def sql(self,columnMap):
    return "(%s %s %s)" % (self.criteria1.sql(columnMap), AndSearchCriteria.SQL_AND, self.criteria2.sql(columnMap))

class OrSearchCriteria(SearchCriteria):
  SQL_OR = "OR"
  def __init__(self, criteria1, criteria2):
    self.criteria1 = criteria1
    self.criteria2 = criteria2
  def accepts(self, obj):
    return self.criteria1.accepts(obj) or self.criteria2.accepts(obj)
  def sql(self,columnMap):
    return "(%s %s %s)" % (self.criteria1.sql(columnMap), OrSearchCriteria.SQL_OR, self.criteria2.sql(columnMap))

class NotSearchCriteria(SearchCriteria):
  SQL_NOT = "NOT"
  def __init__(self, criteria1):
    self.criteria1 = criteria1
  def accepts(self, obj):
    return self.criteria1.accepts(obj)
  def sql(self,columnMap):
    return "(%s %s)" % (NotSearchCriteria.SQL_NOT, self.criteria1.sql(columnMap))

class NotNullCriteria(SearchCriteria):
  def __init__(self, property):
    self.property = property
  def accepts(self, obj):
    return True
  def sql(self,columnMap):
    return "(%s is NOT NULL)" % (columnMap[self.property])

class NullCriteria(SearchCriteria):
  def __init__(self, property):
    self.property = property
  def accepts(self, obj):
    return True
  def sql(self,columnMap):
    return "(%s is NULL)" % (columnMap[self.property])

