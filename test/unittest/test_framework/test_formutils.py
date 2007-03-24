import unittest, os, warnings, pmock
from pmock import *

from pywebmvc.framework.core import *
from pywebmvc.framework import formutils
from pywebmvc.unittest.testutils import *



class TestFormutils(PyWebMvcTestCase):
  def getRequestObject(self):
    req = self.mock()
    options = {
      "pyWebMvcConfig" : "test/data/config.xml",
      "pyWebMvcExtension" : "tst"
    }
    req.get_options = lambda: options
    return req
        
  def testHref(self):
    request = self.getRequestObject()
    self.assertEquals(formutils.href(request, "stubbed"),"/stubbed.tst")
    request.verify()
  def testWithListParams(self):
    request = self.getRequestObject()
    params = [("one","1"),("two", "2")]
    self.assertEquals(formutils.href(request, "stubbed", params),"/stubbed.tst?one=1&two=2")
    request.verify()
  def testWithDictParams(self):
    request = self.getRequestObject()
    params = {
      "one":"1",
      "two":"2"
    }
    url = formutils.href(request, "stubbed", params)
    self.assertUrlParameter(url, "one", "1")
    self.assertUrlParameter(url, "two", "2")
    request.verify()

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(loader.loadTestsFromTestCase(TestFormutils))
