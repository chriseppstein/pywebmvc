"""Utilities used by pywebmvc."""

import weakref, inspect, types
from copy import copy
from UserDict import UserDict

class MetaInstanceTracker(type):
    """Metaclass for tracking instances"""
    def __new__(cls, name, bases, ns):
        t = super(MetaInstanceTracker, cls).__new__(cls, name, bases, ns)
        t.__instance_refs__ = []
        return t
    def __instances__(self):
        instances = [(r, r()) for r in self.__instance_refs__]
        instances = filter(lambda (x,y): y is not None, instances)
        self.__instance_refs__ = [r for (r, o) in instances]
        return [o for (r, o) in instances]
    def __call__(self, *args, **kw):
        instance = super(MetaInstanceTracker, self).__call__(*args, **kw)
        self.__instance_refs__.append(weakref.ref(instance))
        return instance

class InstanceTracker:
    """base class for classes which track their instances"""
    __metaclass__ = MetaInstanceTracker

class MetaAutoReloader(MetaInstanceTracker):
    """metaclass for classes which update their instances to point at a new
    definition when it is reloaded"""
    def __new__(cls, name, bases, ns):
        new_class = super(MetaAutoReloader, cls).__new__(
            cls, name, bases, ns)
        f = inspect.currentframe().f_back
        for d in [f.f_locals, f.f_globals]:
            if d.has_key(name):
                old_class = d[name]
                for instance in old_class.__instances__():
                    instance.change_class(new_class)
                    new_class.__instance_refs__.append(
                        weakref.ref(instance))
                # this section only works in 2.3
                for subcls in old_class.__subclasses__():
                    newbases = ()
                    for base in subcls.__bases__:
                        if base is old_class:
                            newbases += (new_class,)
                        else:
                            newbases += (base,)
                    subcls.__bases__ = newbases
                break
        return new_class

class AutoReloader(object):
    """Base class for objects which reload their instances when class
    definitions are reloaded"""
    __metaclass__ = MetaAutoReloader
    def change_class(self, new_class):
        self.__class__ = new_class

class PyWebMvcObject(AutoReloader):
  """Base class for all PyWebMVC objects."""
  pass

class MultiDictValue(object):
  """Tracks the values stored for a given key in the L{MultiDict}."""
  def __init__(self, *args):
    super(MultiDictValue,self).__init__()
    self.values = list(args)
  def __len__(self):
    return len(self.values)
  def add(self, value):
    self.values.append(value)

class MultiDict(UserDict):
  """A dictionary where the set doesn't overwrite the current value, instead it
  accumulates the values in a list. The value stored is converted to a list
  once the second set is done on a particular key."""
  def __setitem__(self, key, value):
    if self.data.has_key(key):
      self.data[key].add(value)
    else:
      self.data[key] = MultiDictValue(value) 
  def __getitem__(self, key):
    item = self.data[key]
    if len(item) > 1:
      return copy(item.values)
    else:
      return item.values[0]

class TabIndexTable(PyWebMvcObject):
  """Tracks the tab-indexes for the fields in a form."""
  def __init__(self):
    self.count = 1
    self.fieldDict = {}
    self.indexDict = MultiDict()

  def add(self, name, index = None):
    """add a field named C{name} with a tab index of C{index}. If index is not
    specified, it will be assigned the index in the order of the unspecified
    fields in the form. TODO: make all the unspecified fields come after the
    specified fields (as it is in html) -- currently they come first."""
    if index is None:
      while self.indexDict.has_key(self.count):
        self.count += 1
      index = self.count
    self.fieldDict[name] = index
    self.indexDict[index] = name

  def lookup(self, name):
    """get the index of field C{name}."""
    return self.fieldDict[name]

  def lookupFields(self, index):
    """get the field or fields having index C{index}. If multiple fields have
    been assigned to this index, a list of strings is returned instead of a
    string."""
    fields = self.indexDict[index]
    if isinstance(fields,types.ListType):
      return fields
    else:
      return [fields]
