import unittest, os, warnings, pmock

from pywebmvc.framework.core import *
from pywebmvc.framework.util import *
from pywebmvc.framework import metadata
from pywebmvc.unittest.testutils import *


class Dummy(object):
  pass

class PyWebMvcObjectTestCase(PyWebMvcTestCase):
  def testReload(self):
    class Foo(PyWebMvcObject):
      def foo(self):
        return "foo"

    fu = Foo()
    self.assertEquals(fu.foo(), "foo")

    class Foo(PyWebMvcObject):
      def foo(self):
        return "bar"

    self.assertEquals(fu.foo(), "bar")

class MultiDictTestCase(PyWebMvcTestCase):
  def testMultiDictWithOneValue(self):
    d = MultiDict()
    d["a"] = 1
    d["b"] = 2
    self.assertEquals(d["a"],1)
    self.assertEquals(d["b"],2)
    keyErrorRaised = False
    try:
      d["c"]
    except KeyError:
      keyErrorRaised = True
    self.assertTrue(keyErrorRaised)
  def testMultiDictWithManyValues(self):
    d = MultiDict()
    d["a"] = 1
    d["b"] = 2
    d["a"] = 3
    self.assertTrue(1 in d["a"])
    self.assertTrue(3 in d["a"])
    self.assertEquals(d["b"],2)
    del d["b"]
    keyErrorRaised = False
    try:
      d["b"]
    except KeyError:
      keyErrorRaised = True
    self.assertTrue(keyErrorRaised)

class TabIndexTableTestCase(PyWebMvcTestCase):
  def testImplicit(self):
    table = TabIndexTable()
    table.add("a")
    table.add("b")
    table.add("c")
    self.assertEquals(table.lookup("a"),1)
    self.assertEquals(table.lookup("b"),2)
    self.assertEquals(table.lookup("c"),3)
  def testExplicit(self):
    table = TabIndexTable()
    table.add("a",2)
    table.add("b")
    table.add("c")
    table.add("d",3)
    self.assertEquals(table.lookup("a"),2)
    self.assertEquals(table.lookup("b"),1)
    self.assertEquals(table.lookup("c"),3)
    self.assertEquals(table.lookup("d"),3)
    self.assertTrue("b" in table.lookupFields(1))
    self.assertTrue("a" in table.lookupFields(2))
    self.assertTrue("c" in table.lookupFields(3))
    self.assertTrue("d" in table.lookupFields(3))

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(loader.loadTestsFromTestCase(PyWebMvcTestCase))
suite.addTest(loader.loadTestsFromTestCase(MultiDictTestCase))
suite.addTest(loader.loadTestsFromTestCase(TabIndexTableTestCase))

