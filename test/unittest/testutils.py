"""Test Cases and utilities for performing unit testing and functional testing
against a PyWebMVC-based application."""
import unittest, os, warnings, pmock, urllib, urllib2, htmllib, re, cookielib, urlparse


from pywebmvc.framework.core import *
from formatter import NullFormatter

class PyWebMvcTestCase(pmock.MockTestCase):
  def assertNone(self, value):
    self.assertEqual(value, None)
  def assertUrlParameter(self, url, name, value):
    queryArgs = urlparse.urlsplit(url)[3]
    valueFound = None
    for arg in queryArgs.split("&"):
      (n, v) = arg.split("=")
      (n, v) = (urllib.unquote(n), urllib.unquote(v))
      if n == name:
        valueFound = v
        if valueFound == value:
          break
    else:
      if not valueFound:
        self.fail("Url Parameter %s was not found in %s." % (name, url))
      else:
        self.fail(("Parameter value found (%s) did not match expected (%s) "
        "for parameter %s.") %(
          valueFound, value, name
        ))
        


class ServletTestCase(PyWebMvcTestCase):
  def setUp(self):
    from pywebmvc.framework.formutils import FieldStorage
    self.setUpRequest()
    self.form = FieldStorage(self.request)
    self.request.form = self.form
    self.config = self.mock()
    self.mapping = self.getActionMapping(self.config)
  def setUpRequest(self):
    self.request = self.mock()
    self.request.args = ""
    self.request.method = "GET"
    self.request.options = {}
    self.request.get_options = lambda : self.request.options
  def getActionMapping(self, config):
    return ActionMapping("actionId", "/path/to/action", self.getActionClass(),
      config)

class ActionTestCase(ServletTestCase):
  """TestCase base class for tesing an
  L{action<pywebmvc.framework.core.Action>} by direct execution (outside of the
  mod_python container)."""
  def setUp(self):
    super(ActionTestCase,self).setUp()
    self.action = self.mapping.createInstance()
  def getActionClass(self):
    return Action
  def performAction(self):
    self.forward = self.action(self.request, self.mapping)
  def verifyForward(self, forwardId):
    if forwardId is None:
      self.assertNone(self.forward)
      return
    self.assertEqual(self.forward, self.mapping[forwardId])

class ValidationResultParser(htmllib.HTMLParser):
  def __init__(self):
    htmllib.HTMLParser.__init__(self,NullFormatter())
    self.inResultDiv = 0
    self.valid = False
  def start_div(self, attrs):
    if self.inResultDiv > 0:
      self.inResultDiv += 1
      return
    for n, v in attrs:
      if n == "id" and v == "result":
        self.inResultDiv = 1
        return
  def end_div(self):
    if self.inResultDiv > 0:
      self.inResultDiv -= 1
  def start_h2(self, attrs):
    if self.inResultDiv > 0:
      for n, v in attrs:
        if n == "class" and v == "valid":
          self.valid = True
          return
  def isValid(self):
    return self.valid

class HtmlPageTestCase(ServletTestCase):
  """TestCase base class for tesing an
  L{HtmlPage<pywebmvc.framework.core.HtmlPage>} by direct execution (outside of
  the mod_python container). The returned HTML is submitted to the W3C html
  validator and fails if the validator does not consider it to be valid."""
  def setUp(self):
    super(HtmlPageTestCase,self).setUp()
    self.page = self.getPageClass()()
  def getPageClass(self):
    return HtmlPage
  def getActionClass(self):
    return Action
  def validateHtml(self, html):
    params = {}
    params["fragment"] = html
    params["submit"] = "Check"
    data =  urllib.urlencode(params)
    url = 'http://validator.w3.org/check'
    stream = urllib2.urlopen(url, data)
    response = stream.read()
    stream.close()
    validationResultParser = ValidationResultParser()
    validationResultParser.feed(response)
    self.assertTrue(validationResultParser.isValid())

class ActionTester(object):
  """This class performs HTTP level testing of actions against the running
  web server (in-container testing). Utility methods are provided for
  testing the response."""
  def get_opener(self):
    """Override this if you need to control the opening behavior (e.g. basic
    authentication, proxies, etc.)"""
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
    return opener
  def __init__(self, config, host = "localhost", protocol = "http", port = None ):
    """Tell the Tester where to find the running server."""
    self.config = config
    self.host = host
    self.protocol = protocol
    self.port = port
    self.cookieJar = cookielib.CookieJar()
    urllib2.install_opener(self.get_opener())
    self.testedActions = {}
  def getFullUrl(self,absoluteUrl, data=None):
    """Constructs a url given an absolute path and server info provided to the
    constructor."""
    fullUrl = self.protocol +"://" + self.host
    if self.port:
      fullUrl += ":"+self.port
    fullUrl += absoluteUrl
    if data:
      fullUrl += "?" + urllib.urlencode(data)
    return fullUrl
  def getActionUrl(self, actionId):
    """convenience method for getting the server-relative url path to an
    action."""
    return self.config.getActionMapping(actionId).getUrl()
  def get(self, actionId, data=None):
    """Performs a GET request on the url after performing url resolution.
    C{data} is a list of pairs or a dict with the URL query parameters to be
    appended."""
    url = self.getActionUrl(actionId)
    fullUrl = self.getFullUrl(url,data)
    stream = urllib2.urlopen(fullUrl)
    self._storeValues(stream, actionId)
    stream.close()

  def post(self, actionId, params=None):
    """Performs a POST request on the url after performing url resolution.
    C{data} is a list of pairs or a dict with the URL query parameters to be
    posted with the request."""
    data = None
    url = self.getActionUrl(actionId)
    if params:
      data = urllib.urlencode(params)
    stream = urllib2.urlopen(self.getFullUrl(url), data)
    self._storeValues(stream, actionId)
    stream.close()

  def getTestedActions(self):
    """Returns a list of actions which have been tested so far"""
    return self.testedActions.keys()

  def getAccessCount(self, actionId):
    """Tells you how many times a particular action has been accesses by this
    tester."""
    if self.testedActions.has_key(actionId):
      return self.testedActions[actionId]
    else:
      return 0

  def _parseReturnedUrl(self,url):
    lastUrl = urlparse.urlparse(url)[2]
    if self.config.prefix and lastUrl.startswith(self.config.prefix):
      lastUrl = lastUrl[len(self.config.prefix):]
    if lastUrl.endswith(self.config.extension):
      lastUrl = lastUrl[:-(len(self.config.extension)+1)]
    return lastUrl

  def _storeValues(self, stream, actionId):
    self.lastResponse = stream.read()
    self.lastUrl = self._parseReturnedUrl(stream.geturl())
    try:
      self.lastAction = self.config.getActionMappingByPath(self.lastUrl).id
    except KeyError:
      self.lastAction = None
    if self.testedActions.has_key(actionId):
      self.testedActions[actionId] = self.testedActions[actionId] + 1
    else:
      self.testedActions[actionId] = 1

class HttpTestSuite(unittest.TestSuite):
  """This test suite must be used when performing in container testing. To use
  it with a standard C{unitest.TestLoader} do the following::
    loader = unittest.TestLoader()
    loader.suiteClass = HttpTestSuite
    suite = loader.loadTestsFromTestCase(MyHttpTestCase)
  """
  def setTester(self, tester):
    for test in self:
      test.setTester(tester)

class HttpTestCase(unittest.TestCase):
  """This test case base class provides the functionality to perform
  in-container by accessing an action and performing asserts against the
  reponse. Unhandled HTTP response codes (500, 404, etc.) are treated as
  errors."""
  def setTester(self, tester):
    """usually called indirectly by the test
    L{suite<HttpTestSuite.setTester>}."""
    self.tester = tester
  def get(self, actionId, data=None):
    """perform an HTTP GET on the specified C{actionId}. Query arguments are
    provided by C{data} as a list of (name,value) tuples or a dict of
    {"name":"value"} mappings."""
    self.tester.get(actionId, data)
  def post(self, actionId, data=None):
    """perform an HTTP POST on the specified C{actionId}. Query arguments are
    provided by C{data} as a list of (name,value) tuples or a dict of
    {"name":"value"} mappings."""
    self.tester.post(actionId,data)
  def assertResponseContains(self, patString):
    """assert that the response contains C{patString} which can be a substring
    or a regular expression string."""
    self.assertTrue(re.search(patString, self.tester.lastResponse),
                    "'%s' was not found" % patString)
  def failIfResponseContains(self, patString):
    """opposite of L{assertResponseContains}"""
    self.failIf(re.search(patString, self.tester.lastResponse),
                "'%s' was found" % patString)
  def assertLastUrl(self, urlString):
    """assert that the server redirected you to the C{urlString}. Not usually
    used. See L{assertLastAction}."""
    self.assertEqual(urlString,self.tester.lastUrl,
      """The last URL "%s" didn't match the expected URL "%s\"""" %
        (self.tester.lastUrl, urlString))
  def assertLastAction(self, actionId):
    """assert that the server redirected you the action specified by actionId"""
    self.assertEqual(actionId,self.tester.lastAction,
      """The last action %s didn't match the expected action %s""" %
        (repr(self.tester.lastAction), repr(actionId)))
  def printLastResponse(self):
    """convenience method for debugging purposes."""
    print(self.tester.lastResponse)


class DefaultHttpTestCase(HttpTestCase):
  """Used in conjunction with L{getUntestedActionsSuite}, This class performs
  basic automated testing on the actionId specified in the constructor."""
  def __init__(self, actionId, tester, setUpFunc, tearDownFunc, verifyFunc):
    super(DefaultHttpTestCase,self).__init__()
    self.actionId = actionId
    self.tester = tester
    self.setUpFunc = setUpFunc
    self.tearDownFunc = tearDownFunc
    self.verifyFunc = verifyFunc
  def id(self):
    return self.actionId
  def shortDescription(self):
    return "Accesses '%s' and raises an error if any HTTP error code is returned." % self.actionId
  def setUp(self):
    if self.setUpFunc:
      self.setUpFunc()
  def tearDown(self):
    if self.tearDownFunc:
      self.tearDownFunc()
  def verify(self):
    if self.verifyFunc:
      self.verifyFunc(self.tester, self)
    else:
      self.assertLastAction(self.actionId)
  def runTest(self):
    """Accessess the action. An exception is raised if the server returns
    an error response code."""
    self.tester.get(self.actionId)
    self.verify()

def getUntestedActionsSuite(tester, setUp = None, tearDown = None, verify = None):
  """Returns a test suite that will attempt to access any actions defined
  in the application configuration but not yet accessed by
  L{tester<ActionTester>}.  If the callable C{setUp} is provided, it will be
  invoked before each action is accessed. If the callable C{tearDown} is
  provided, it will be invoked after each action is accessed. C{verify} is a
  callable which must accept two arguments: a L{tester<ActionTester>} for
  accessing the response and a L{HttpTestCase} for performing assertions.
  If you do not want to have an action tested set the attribute C{skipAutoTest}
  for the action to any value.
  """
  suite = HttpTestSuite()
  actionIds = [action.id for action in tester.config.getActionMappings()]
  actionIds.sort()
  for actionId in actionIds:
    if not tester.config.getActionMapping(actionId).hasAttribute("skipAutoTest") and \
       tester.getAccessCount(actionId) == 0:
      suite.addTest(DefaultHttpTestCase(actionId, tester, setUp, tearDown, verify))
  return suite
