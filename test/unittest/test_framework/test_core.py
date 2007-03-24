import unittest, os, warnings, pmock

from pywebmvc.framework.core import *
from pywebmvc.framework import metadata
from pywebmvc.unittest.testutils import *


class Dummy(object):
  pass

class TestExceptions(PyWebMvcTestCase):
  def testPyWebMvcException(self):
    message = "Test"
    exception = PyWebMvcException(message)
    self.assertTrue(isinstance(exception,Exception))
    self.assertEquals(str(exception), message)
  def testActionNotFoundException(self):
    path = "/test/action.ptz"
    exception = ActionNotFoundException(path)
    self.assertTrue(isinstance(exception,PyWebMvcException))
    self.assertTrue(str(exception).find(path) > 0)
  def testPyWebMvcInvalidConfigurationException(self):
    message = "foo"
    exception = PyWebMvcInvalidConfigurationException(message)
    self.assertTrue(isinstance(exception,PyWebMvcException))

class TestErrorHandler(PyWebMvcTestCase):
  def testErrorHandler(self):
    klass = Dummy
    forward = "asdf"
    errorHandler = ErrorHandler(klass, forward)
    self.assertEqual(errorHandler.exceptionClass, klass)
    self.assertEqual(errorHandler.forward, forward)

class TestActionMapping(PyWebMvcTestCase):
  def setUp(self):
    self.id = "actionId"
    self.path = "/path/to/action.ptz"
    self.pythonClass = Dummy
    self.config = self.mock()
    self.formMetadata = None
    self.rendererFactory = None
    self.actionMapping = ActionMapping(self.id,
      self.path, self.pythonClass, self.config,
      self.formMetadata, self.rendererFactory)
  def testConstructor(self):
    self.assertEqual(self.id, self.actionMapping.id)
    self.assertEqual(self.path, self.actionMapping.path)
    self.assertEqual(self.pythonClass, self.actionMapping.pythonClass)
    self.assertEqual(self.formMetadata, self.actionMapping.formMetadata)
    self.assertEqual(self.rendererFactory, self.actionMapping.rendererFactory)
    self.assertTrue(len(self.actionMapping.forwards) == 0)
    self.assertTrue(len(self.actionMapping.attributes) == 0)
  def testAddLocalForward(self):
    key = "test"
    forward = self.mock()
    self.actionMapping.addLocalForward(key, forward)
    self.assertEquals(self.actionMapping[key],forward)
  def testAddDuplicateLocalForward(self):
    key = "test"
    forward = self.mock()
    self.actionMapping.addLocalForward(key, forward)
    exceptionRaised = False
    try:
      self.actionMapping.addLocalForward(key, forward)
    except PyWebMvcInvalidConfigurationException, e:
      exceptionRaised = True
    self.assertTrue(exceptionRaised)
  def testNoSuchForward(self):
    exceptionRaised = False
    self.config.globalForwards = {}
    try:
      self.actionMapping.findForward("notamappingid")
    except KeyError:
      exceptionRaised = True
    self.assertTrue(exceptionRaised)
  def testFindGlobalForward(self):
    exceptionRaised = False
    key = "gFwd"
    globalFwd = self.mock()
    self.config.globalForwards = {key: globalFwd}
    self.assertEqual(globalFwd,self.actionMapping[key])
  def testCreateInstance(self):
    instance = self.actionMapping.createInstance()
    self.assertTrue(isinstance(instance, Dummy))
  def testAttributes(self):
    key1 = "key1"
    value1 = "value1"
    key2 = "key2"
    value2 = "value2"
    self.actionMapping.setAttribute(key1, value1)
    self.actionMapping.setAttribute(key2, value2)
    self.assertTrue(self.actionMapping.hasAttribute(key1))
    self.assertTrue(not self.actionMapping.hasAttribute("nosuchkey"))
    self.assertEqual(self.actionMapping.getAttribute(key1),value1)
    self.assertEqual(self.actionMapping.getAttribute(key2),value2)
    exceptionRaised = False
    try:
      self.actionMapping.getAttribute("nosuchkey")
    except KeyError, e:
      exceptionRaised = True
    self.assertTrue(exceptionRaised)
  def testGetUrl(self):
    self.config.prefix = None
    self.config.extension = "ptz"
    self.assertEqual(self.path+".ptz",self.actionMapping.getUrl())

class TestActionErrors(PyWebMvcTestCase):
  def setUp(self):
    self.errors = ActionErrors()
  def testConstructor(self):
    self.assertEquals(len(self.errors),0)
  def testActionErrors(self):
    key1 = ActionError.GLOBAL
    msg1 = "Error Message #1"
    key2 = "key2"
    msg2 = "Error Message #2"
    key4 = key2
    msg4 = "Error Message #4"
    key3 = "key3"
    msg3 = "Error Message #3"
    index3 = 0
    self.errors.add(ActionError(key1, msg1))
    self.errors.add(ActionError(key2, msg2))
    self.errors.add(ActionError(key3, msg3, index3))
    self.errors.add(ActionError(key4, msg4))
    self.assertTrue(self.errors.hasError(key1))
    self.assertTrue(self.errors.hasError(key2))
    self.assertTrue(self.errors.hasError(key3))
    self.assertTrue(self.errors.hasError(key3, index3))
    self.assertTrue(not self.errors.hasError("nosuchkey"))
    self.assertTrue(not self.errors.hasError(key3, index3 + 1))
    self.assertEqual(len(self.errors.getErrors(key2)), 2)

class ConcreteDispatchAction(DispatchAction):
  def concrete(self, req, mapping):
    return mapping["success"]

class TestDispatchAction(ActionTestCase):
  def setUp(self):
    super(TestDispatchAction,self).setUp()
  def getActionClass(self):
    return ConcreteDispatchAction
  def testDispatchWithMissingParameter(self):
    exceptionRaised = False
    try:
      self.performAction()
    except PyWebMvcException:
      exceptionRaised = True
    self.assertTrue(exceptionRaised)
  def testDispatch(self):
    self.request.charset = "utf-8"
    self.form["do"] = "concrete"
    self.mapping.addLocalForward("success",LocalForward(self.config,"foo"))
    self.performAction()
    self.verifyForward("success")
  
class TestDefaultPage(HtmlPageTestCase):
  def testPage(self):
#    self.request.expects(pmock.at_least_once()).method("get_options").will(pmock.return_value({}))
    self.request.charset = "utf-8"
    html = self.page.render(self.request, self.mapping)
    self.validateHtml(html)

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(loader.loadTestsFromTestCase(TestExceptions))
suite.addTest(loader.loadTestsFromTestCase(TestErrorHandler))
suite.addTest(loader.loadTestsFromTestCase(TestActionMapping))
suite.addTest(loader.loadTestsFromTestCase(TestActionErrors))
suite.addTest(loader.loadTestsFromTestCase(TestDispatchAction))
suite.addTest(loader.loadTestsFromTestCase(TestDefaultPage))

