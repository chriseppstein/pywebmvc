#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""mod_python integration for pywebmvc."""
import traceback
import trace, sys, StringIO
import mod_python
from types import *
from util import PyWebMvcObject
from core import ActionNotFoundException
from parser import getPyWebMvcConfig
from mod_python import apache as mod_apache
from mod_python import util as mod_util
from mod_python.Session import Session
from mod_python.util import Field
from resourcebundle import BundleManager

def sendRedirect(req, path):
  """simple wrapper for mod_python's redirect that is more similar to jsp."""
  #str:ok
  mod_util.redirect(req,str(path))

class ApacheOut(PyWebMvcObject):
  """Write to the apache log file as a file object.

  Please note:
    - Do not attempt to close this file.
    - This will write to your main apache error log, and not to any
      logs which are virtual-server based.
  """
  def write(self,msg):
    mod_apache.log_error(msg.expandtabs(2).rstrip())

apacheOut = ApacheOut()

class Logger:
  """ This class implements a singleton that provides convenient access to apache logging services.  It eliminates the need to pass the apache request to functions just to get logging. To use this class without errors setRequest must be called (preferably by the handler class) before any logging functions are called. """

  __request = None

  def setRequest(req):
    Logger.__request = req
  setRequest = staticmethod(setRequest)

  def debug(msg, callingObj = None):
    Logger.__request.log_error(msg, mod_apache.APLOG_DEBUG)
  debug = staticmethod(debug)

  def info(msg, callingObj = None):
    Logger.__request.log_error(msg, mod_apache.APLOG_INFO)
  info = staticmethod(info)

  def warn(msg, callingObj = None):
    Logger.__request.log_error(msg, mod_apache.APLOG_WARNING)
  warn = staticmethod(warn)

  def error(msg, callingObj = None):
    Logger.__request.log_error(msg, mod_apache.APLOG_ERR)
  error = staticmethod(error)

class FieldStorage(mod_python.util.FieldStorage):
  #   def __init__(self, req, keep_blank_values=0, strict_parsing=0, file_callback=None, field_callback=None):
  #     try:
  #       mod_python.util.FieldStorage.__init__(self, req, keep_blank_values, strict_parsing, file_callback, field_callback)
  #     except mod_python.apache.SERVER_RETURN, value:
  #       req.log_error("Got FieldStorage exception %s " % value)
  #       if value != mod_python.apache.HTTP_NOT_IMPLEMENTED:
  #         raise
  #     req.log_error("FieldStorage = %s" % (self))

  """Adds field setting to the mod_python FieldStorage class"""
  def __init__(self, req = None, keep_blank_values=0, strict_parsing=0, file_callback=None, field_callback=None, defaultCharset = None, initialValues = None):
    if defaultCharset:
      self.defaultCharset = defaultCharset
    elif req:
      self.defaultCharset = req.charset
    else:
      self.defaultCharset = "utf-8"
    if req is None:
      self.list = []
    else:
      try:
        mod_python.util.FieldStorage.__init__(self, req, keep_blank_values, strict_parsing, file_callback, field_callback)
      except TypeError:
        assert file_callback is None and field_callback is None
        #backwards compatible initialization to old mod_python FieldStorage
        mod_python.util.FieldStorage.__init__(self, req, keep_blank_values, strict_parsing)
    if initialValues and hasattr(initialValues, "keys"):
      for key in initialValues.keys():
        self[key] = initialValues[key]
    elif initialValues:
      for (key, value) in initialValues:
        self[key] = value
    self.original_list = self.list[:]
  def __delitem__(self, key):
    if self.list is None:
      raise TypeError, "not indexable"
    newList = []
    for item in self.list:
      if item.name != key:
        newList.append(item)
    self.list = newList
  def __setitem__(self, key, value):
    """Dictionary style index setting."""
    del self[key]
    if isinstance(value, NoneType):
      return
    if isinstance(value, StringTypes):
      file = StringIO.StringIO(self.encode(value))
      self.list.append(Field(key, file, "text/plain", {}, None, {}))
    elif isinstance(value, ListType) or isinstance(value, TupleType):
      for v in value:
        if isinstance(v, StringTypes):
          file = StringIO.StringIO(v)
          self.list.append(Field(key, file, "text/plain", {},
                                 None, {}))
    else:
      raise TypeError, "invalid type for set: strings or sequences of strings"
  def getCharset(self):
    if not hasattr(self,"charset"):
      self.charset = self.defaultCharset
      for item in self.list:
        if item.name == "_charset_":
          if item.value:
            self.charset = item.value
          break
    return self.charset
  def decode(self, value):
    if not isinstance(value,StringTypes):
      value = unicode(value)
    value = value.decode(self.getCharset())
    return value
  def encode(self, value):
    if not isinstance(value,StringTypes):
      value = unicode(value)
    value = value.encode(self.getCharset())
    return value
  def __getitem__(self, key):
    """Dictionary style indexing."""
    if self.list is None:
        raise TypeError, "not indexable"
    found = []
    for item in self.list:
        if item.name == "_charset_":
          continue
        elif item.name == key:
            if isinstance(item.file, FileType) or \
                   isinstance(getattr(item.file, 'file', None), FileType):
                found.append(item)
            else:
                found.append(item.value)
    decodedlist = []
    for item in found:
      if hasattr(item,"file"):
        decodedlist.append(item)
      else:
        decodedlist.append(self.decode(item))
    found = decodedlist
    if not found:
        raise KeyError, key
    if len(found) == 1:
        return found[0]
    else:
        return found
  def keys(self):
      """Dictionary style keys() method."""
      if self.list is None:
          raise TypeError, "not indexable"
      keys = []
      for item in self.list:
          if item.name == "_charset_": continue
          if item.name not in keys: keys.append(item.name)
      return keys
  def __unicode__(self):
    result = u""
    for key in self.keys():
      result += u"%s=%s," % (key, self[key])
    return result
  def reset(self):
    self.list = self.original_list[:]

class ActionHandler(PyWebMvcObject):
  """A mod_python handler class for passing control to a PyWebMVC L{Action<core.Action>}"""
  def __init__(self):
    self.bundleManager = None
  def getExtension(self, req):
    """reads the path extension from the apache config file.

    The option C{pyWebMvcExtension} is used to indicate the extension.
    For example:

    C{PythonOption pyWebMvcExtension ptz}

    This should be set only once per server/virtual-server.
    """
    options = req.get_options()
    if options.has_key("pyWebMvcExtension"):
      return options["pyWebMvcExtension"]
    else:
      return None
  def getSessionSecret(self, req):
    """reads the session secret from the apache config file.

    The option C{sessionSecret} is used to indicate the extension.
    For example:

    C{PythonOption sessionSecret foo}

    This should be set only once per server/virtual-server.
    """
    options = req.get_options()
    if options.has_key("sessionSecret"):
      return options["sessionSecret"]
    else:
      return None
  def getSessionTimeout(self, req):
    """reads the session timeout from the apache config file.

    The option C{sessionTimeout} is used to indicate the duration of
    a session in seconds before it times out.
    For example:

    C{PythonOption sessionTimeout 1800}

    Sets the timeout for 30 minutes.
    This should be set only once per server/virtual-server.
    """
    options = req.get_options()
    if options.has_key("sessionTimeout"):
      return int(options["sessionTimeout"])
    else:
      return 1800
  def authorized(self, req, mapping):
    """Base implementation for performing authorization.
    Should return C{True} if the access is authorized, C{False} otherwise.

    Default implementation always returns C{True}.
    """
    return True
  def redirectMaybe(self, req, mapping):
    """Base implementation for performing application-state-based redirects.
    Should return C{None} if there is no redirect for the request, otherwise an
    L{ActionForward<core.ActionForward>} object.

    Default implementation always returns C{None}.
    """
    return None
  def checkAuthentication(self,req, mapping):
    """Base implementation for requiring form-based authentication to access
    a resource. This implementation checks the apache configuration for this
    request to see if the C{pyWebMvcAuthentication} option is set to
    C{required}. If required, the user will be redirected to the login action
    as specified by the C{authenticationForward} option. Any form data will be
    persisted and reused after authentication is successful. For example::

      <LocationMatch "/secure/.*">
        PythonOption authenticationForward login
        PythonOption pyWebMvcAuthentication required
      </LocationMatch>

    Would require authentication for all urls beginning with C{/secure/} by
    redirecting the user to the C{login} L{Action<core.Action>}. These options
    may be set in any apache context.
    """
    options = req.get_options()
    if options.has_key("pyWebMvcAuthentication") and \
       options["pyWebMvcAuthentication"] == "required":
      if not (req.session.has_key("authenticated") and
              req.session["authenticated"]):
        if mapping.hasAttribute("onAuthenticationFailure") and \
           mapping.getAttribute("onAuthenticationFailure") == "fail" \
           or not options.has_key("pyWebMvcAuthenForward"):
          raise mod_apache.SERVER_RETURN, mod_apache.HTTP_FORBIDDEN
        else:
          req.session["authenticationForward"] = mapping.id
          dict = {}
          for key in req.form.keys():
            dict[key] = req.form[key]
          req.session["authenticationForm"] = dict
          req.session.save()
          loginMapping = mapping.config.getActionMapping(
            options["pyWebMvcAuthenForward"])
          sendRedirect(req, loginMapping.getUrl())
      else:
        saveSession = False
        if req.session.has_key("authenticationForward"):
          del req.session["authenticationForward"]
          saveSession = True
        if req.session.has_key("authenticationForm"):
          savedForm = req.session["authenticationForm"]
          del req.session["authenticationForm"]
          for key in savedForm.keys():
            req.form[key] = savedForm[key]
          saveSession = True
        if saveSession:
          req.session.save()
  def __call__(self, req):
    """Default handler function for mod_python. Mostly this function
    passes control to L{handleRequest}."""
    Logger.setRequest(req)
    try:
      options = req.get_options()
      if options.has_key("pyWebMvcProfile") and \
        options["pyWebMvcProfile"].lower() in ("true", "on", "yes"):
        import profile
        outFile = open("/tmp/pywebmvc.profile","a")
        outFile.write(
"""============================================================
Profile results for %s
============================================================
""" % (req.uri))
        sys.stdout = outFile
        try:
          profile.runctx('locals()["rt"] = self.handleRequest(req)',globals(),locals())
          return locals()["rt"]
        finally:
          sys.stdout = sys.__stdout__
          outFile.close()
      elif options.has_key("pyWebMvcTrace") and \
        options["pyWebMvcTrace"].lower() in ("true", "on", "yes"):
        tracer = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix],
                             trace=1, count=0)
        sys.stdout = apacheOut
        try:
          tracer.runctx('locals()["rt"] = self.handleRequest(req)',globals(),locals())
          return locals()["rt"]
        finally:
          sys.stdout = sys.__stdout__
      else:
        result = self.handleRequest(req)
        self.cleanupRequest(req)
        return result
    finally:
      Logger.setRequest(None)
  def getPath(self, req):
    """Calculates the path suitable for finding an 
    L{action mapping<core.ActionMapping>} in the configuration file.
    """
    path = req.uri
    pyWebMvcExtension = self.getExtension(req)
    if pyWebMvcExtension:
      path = path[:-(len(pyWebMvcExtension)+1)]
    return path
  def getConfig(self, req):
    """Retrieves the singleton L{configuration<core.PyWebMvcConfiguration>}
    object for the application.
    """
    return getPyWebMvcConfig(req)
  def getActionMapping(self, req):
    """Retrieves the L{ActionMapping<core.ActionMapping>} for the given request
    and raises L{KeyError} when not found."""
    config = getPyWebMvcConfig(req)
    path = self.getPath(req)
    return config.getActionMappingByPath(path)
  def handleExceptionMaybe(self, req, e):
    """Local Forwards to an L{ErrorHandler<core.ErrorHandler>} for the
    exception C{e} based on the handlers specified in the application
    configuration. Returns C{None} when the exception is not handled.
    """
    if isinstance(e, mod_apache.SERVER_RETURN):
      return None
    config = getPyWebMvcConfig(req)
    for handler in config.errorHandlers:
      if handler.shouldHandle(req, e):
        forward = handler.handle(req, e)
        return self.doForward(forward, req, forward.mapping)
    return None
  def getCharset(self,req):
    """This function returns the charset set as::
      PythonOption pyWebMvcDefaultCharset <charset>
    and defaults to utf-8 if not set.
    TODO: charset negotiation.
    """
    options = req.get_options()
    charset = "utf-8"
    if options.has_key("pyWebMvcDefaultCharset"):
      charset = options["pyWebMvcDefaultCharset"]
    return charset
  def prepareRequest(self, req):
    """Initializes the mod_python request object to have the PyWebMVC-related
    attributes set. Initializes the session on first access.
    """
    # this "if" check is necessary because if the Session has already been
    # created by a derived class, mod_python will hang.
    if hasattr(req, "alreadyPrepared"):
      return
    else:
      req.alreadyPrepared = True

    req.charset = self.getCharset(req)
    req.form = FieldStorage(req,1,False)

    options = req.get_options()
    if options.has_key("pyWebMvcDebug") and options["pyWebMvcDebug"].lower() in ("true", "on", "yes"):
      #str:ok
      req.log_error("Form values = \n" + str(req.form))
      
    req.locale = self.getRequestLocale(req)
    req.bundle = self.getBundle(req)
    req.session = self.retrieveSession(req)
  def retrieveSession(self, req):
    sessionSecret = self.getSessionSecret(req)
    sessionTimeout = self.getSessionTimeout(req)
    session = Session(req,secret=sessionSecret,timeout=sessionTimeout)
    session.save()
    return session
  def getRequestLocale(self, req):
    config = getPyWebMvcConfig(req)
    preferredLanguages = getPreferredLanguages(req)
    locale = config.bundleManager.negotiateLocale(preferredLanguages)
    return locale
  def getBundle(self, req):
    config = getPyWebMvcConfig(req)
    return config.bundleManager.getBundle(req.locale)
  def cleanupRequest(self, req):
    """Cleans up the mod_python session. Also disassociates the request from the Logger"""
    if hasattr(req, "session"):
      req.session.unlock()
    Logger.setRequest(None)
  def handleRequest(self, req):
    """This is the main request handling routine for all actions. It implements
    a strategy that sub classes should adhere to by overriding the individual
    methods of the strategy instead of this handler."""
    config = getPyWebMvcConfig(req)
    try:
      try:
        self.prepareRequest(req)
        actionMapping = self.getActionMapping(req)
        self.checkAuthentication(req,actionMapping)
        if not self.authorized(req, actionMapping):
          return mod_apache.HTTP_FORBIDDEN
        forward = self.redirectMaybe(req, actionMapping)
        if not forward:
          forward = config.globalForwards[actionMapping.id]
        return self.doForward(forward, req, actionMapping)
      except:
        e = sys.exc_info()[1]
        ret = self.handleExceptionMaybe(req, e)
        if ret is None:
          raise
        else:
          return ret
    except ActionNotFoundException:
      return mod_apache.HTTP_NOT_FOUND
    except:
      if isinstance(sys.exc_info()[1], mod_apache.SERVER_RETURN):
        self.cleanupRequest(req)
        raise
      #no handler found or a non-compliant exception was raised.
      #let mod_python exception handling take over
      #TODO: change this to simple sets on the request and use req.parent to access
      req.err_headers_out.add("EXCEPTION",traceback.format_exc())
      req.err_headers_out.add("FORMDATA",getFormData(req).encode("utf-8"))
      return mod_apache.HTTP_INTERNAL_SERVER_ERROR
  def doForward(self, forward, req, actionMapping = None,
                statusCode = mod_apache.OK):
    """recursive function. This utility function forwards until all of the
    server-side forwards have completed and returns the status code
    specified."""
    if forward:
      if forward.redirect:
        sendRedirect(req, forward.getUrl())
      else:
        nextForward = forward(req, actionMapping)
        if hasattr(nextForward,"mapping") and nextForward.mapping:
          #context change
          actionMapping = nextForward.mapping
          redirectForward = self.redirectMaybe(req,actionMapping)
          if redirectForward:
            nextForward = redirectForward
        return self.doForward(nextForward, req, actionMapping, statusCode)
    else:
      return statusCode

actionHandler = ActionHandler()

def getFormData(req):
  """utility function for printing out the contents of the form"""
  data = ""
  if hasattr(req, "form"):
    for key in req.form.keys():
      data += "%s=%s\n" % (key, req.form[key])
  if not data:
    data = "No form was posted."
  return data

def getPreferredLanguages(req):
  """get the preferred languages of user according to the HTTP specification"""
  langs = []
  try:
    if req.headers_in.has_key("Accept-Language"):
      header = req.headers_in["Accept-Language"]
      for lang in header.split(","):
        #TODO: make sure that the order is enforced by the browser
        lang = lang.split(";")[0]
        langs.append(lang)
  except:
    pass
  return langs
