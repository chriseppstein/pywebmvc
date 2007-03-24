import unittest, os, warnings, pmock, StringIO

from pywebmvc.framework.properties import *
from pywebmvc.unittest.testutils import *


class UnicodePropertiesTestCase(PyWebMvcTestCase):
  def setUp(self):
    self.propertiesText = """normal=This is a normal property.
notunicode1=This \u is not a unicode escape.
notunicode2=This \uZZZZ is not a unicode escape.
unicode1=\\u1111\\u2222\\u3333
unicode2=0\\u11111\\u22222\\u33333
multiline=firstline\\
secondline
"""
    self.properties = Properties()
    self.properties.load(StringIO.StringIO(self.propertiesText))
  def testNormalProperty(self):
    self.assertEquals(self.properties["normal"],"This is a normal property.")
  def testSingleCharEscape(self):
    self.assertEquals(self.properties["notunicode1"],"This u is not a unicode escape.")
  def testUnicodeParseFailure(self):
    self.assertEquals(self.properties["notunicode2"],"This uZZZZ is not a unicode escape.")
  def testUnicodeOnly(self):
    self.assertEquals(self.properties["unicode1"],u"\u1111\u2222\u3333")
  def testMixedUnicode(self):
    self.assertEquals(self.properties["unicode2"],u"0\u11111\u22222\u33333")
  def testMultiline(self):
    self.assertEquals(self.properties["multiline"],"firstlinesecondline")
  def testWrite(self):
    buff = StringIO.StringIO()
    self.properties.store(buff)
    newProps = Properties()
    buff.seek(0)
    newProps.load(buff)
    for prop in self.properties:
      self.assertEquals(self.properties[prop],newProps[prop])

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(loader.loadTestsFromTestCase(UnicodePropertiesTestCase))

