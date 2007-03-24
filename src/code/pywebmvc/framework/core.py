#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""The core classes for the framework."""
import weakref, traceback
import htmlutil
from util import PyWebMvcObject

PYWEBMVC_INTERNAL_ENCODING="utf-8"

class PyWebMvcException(Exception):
  """Base Class Exception for all PyWebMVC exceptions"""
  def __init__(self, message):
    self.message = message
  def __str__(self):
    return unicode(self).encode(PYWEBMVC_INTERNAL_ENCODING)
  def __unicode__(self):
    return unicode(self.message)

class ActionNotFoundException(PyWebMvcException):
  """Raised when a lookup of an action is not found"""
  def __init__(self, path):
    self.path = path
    message = "No action mapping found for path '%s'" % path
    PyWebMvcException.__init__(self, message)

class PyWebMvcInvalidConfigurationException(PyWebMvcException):
  """Raised when the configuration xml file has a semantic error"""
  pass

class ErrorHandler(PyWebMvcObject):
  """Python object for storing the data from the C{<error-handler>} tag in the
  configuration file.  The C{<error-handler>} tag has the following syntax::

    <error-handler exception-class="python.module::class" forward="globalForwardId"/>
  """
  def __init__(self, exceptionClass, forward):
    (self.exceptionClass, self.forward) = (exceptionClass, forward)
  def shouldHandle(self, req, exception):
    return not self.exceptionClass or \
           isinstance(exception, self.exceptionClass)
  def handle(self, req, exception):
    from pywebmvc.framework.parser import getPyWebMvcConfig
    config = getPyWebMvcConfig(req)
    req.exception = exception
    req.stackTrace = traceback.format_exc()
    return config.globalForwards[self.forward]

class ActionMapping(PyWebMvcObject):
  """Python object for storing the mapping of an L{Action} to an URL. It is
  constructed from the C{<action>} tag in the configuation file. The
  C{<action>} tag has the following syntax::
    <action
      id="globalId"
      python-class="python.module::class"
      path="/path/to/my/action"
      form="formMetadataId"
      renderer-factory="rendererFactoryId"
    >
  The action is the where each controller object is defined to handle a
  particular user action. The C{<action>} element is the most important element
  in the config.xml file and is used to associate a url to an L{Action} class.
  The C{<action>} tag accepts the following attributes: id and python-class.
  Additionally, you can provide the following attributes:

    - id - The global L{ActionForward} id of this action mapping.

    - python-class - The class that inherits from L{Action} and implements the
    action logic for this mapping. The syntax for the import is the same as for
    mod_python: C{python.module::klass} is the same as saying C{from
    python.module import klass}.

    - path - The web url from that the controller will pass initial control to
    the action. If the C{PythonOption pyWebMvcExtension} is set in the apache
    configuration then it will be appended to the path provided here.

    - form - Optional. The id of the L{form<metadata.FormMetadata>} that is
      either displayed by or posted to this action.

    - renderer-factory - Optional. The id of the L{renderer
      factory<pywebmvc.framework.render.factory.RendererFactory>} to use for rendering the form
      elements associated with this action.

  Each C{<action>} tag allow the following child elements:

    - C{<attribute>} - defines a name/value pair to be used for customizing
      generic action classes. These attributes can be accessed from the
      C{attributes} property that is a dictionary on the mapping object passed
      into the action handler. An attribute takes the following attributes:
        - name - any string
        - value - any string

    - C{<forward>} - See the documentation on L{LocalForward}.
  """
  def __init__(self, id, path, pythonClass, config, formMetadata = None, rendererFactory=None):
    """Constructor takes the following parameters:
    - C{id} - string
    - C{path} - string
    - C{pythonClass} - the class object referred to by C{python.module::class}.
    - C{config} - a backreference to the
      L{configuration<PyWebMvcConfiguration>}.  Stored as a weak reference.
    - C{formMetadata} - the L{form metadata<metadata.FormMetadata>} object
      referred to by id in the xml.
    - C{rendererFactory} - the L{renderer factory<pywebmvc.framework.render.factory.RendererFactory>}
      object referred to by id in the xml.
    """
    self.config = weakref.proxy(config)
    self.id = id
    self.path = path
    self.pythonClass = pythonClass
    self.formMetadata = formMetadata
    self.rendererFactory = rendererFactory
    self.forwards = {}
    self.attributes = {}
  def getPath(self):
    return self.__path
  def setPath(self, path):
    self.__path = path
  def delPath(self):
    del self.__path
  path = property(getPath, setPath, delPath, "The path of the action mapping as defined in the configuration file")
  def __setitem__(self, key, value):
    """dictionary-style set of the mapping's local forwards"""
    return self.forwards.__setitem__(key,value)
  def __getitem__(self, key):
    """dictionary-style get of the mapping's forwards. Simply calls to L{findForward}.
    """
    return self.findForward(key)
  def createInstance(self):
    """factory-creation method that instantiates the action class for this
    mapping."""
    return self.pythonClass()
  def addLocalForward(self, key, forward):
    """Add a local forward to this mapping. Parameters:
    - key - the id of the local forward. Must be unique within this action
      mapping or L{PyWebMvcInvalidConfigurationException} will be raised.
    - forward - an instance of L{LocalForward}.
    """
    if self.forwards.has_key(key):
      raise PyWebMvcInvalidConfigurationException("Local forward '%s' already exists." % key)
    self.forwards[key] = forward
  def findForward(self, id):
    """struts-style access to look up a forward.  First looks in the local
    forwards and then in the global forwards. Raises L{KeyError} if not found
    in either place."""
    try:
      return self.forwards[id]
    except KeyError:
      return self.config.globalForwards[id]
  def hasForward(self, id):
    """boolean check function to see if a forward would be found by
    L{findForward}."""
    try:
      self.findForward(id)
      return True
    except KeyError:
      return False

  def setAttribute(self, key, value):
    """Store an C{<attribute>} tag for this action mapping."""
    self.attributes[key] = value
  def hasAttribute(self, key):
    """Check to see if an C{<attribute>} tag with a specific name exists for
    this action mapping."""
    return self.attributes.has_key(key)
  def getAttribute(self, key):
    """Retrieve an C{<attribute>} tag with a specific name for this action
    mapping. Raises L{KeyError} if none exists."""
    return self.attributes[key]
  def getUrl(self):
    """Construct the full, server-relative URL for this action mapping.
    """
    url = self.path
    if self.config.prefix:
      url = self.config.prefix + url
    if self.config.extension:
      url += "."+self.config.extension
    return url
  def getFormMetadata(self, req):
    return self.formMetadata

class PageMapping(PyWebMvcObject):
  """A mapping of the global L{ActionForward} id to a L{Page} one of its
  subclasses that knows how to present the particular outcome of an action.
  Each page instance is created just once and used to handle many requests. The
  C{<page>} element takes just attributes, both of that are required:
    - C{id} - The global L{ActionForward} id of this action mapping.
    - C{python-class} - The class that inherits from L{Page}.
  """
  def __init__(self, id, pythonClass):
    """Constructor parameters:
    - id - string.
    - pythonClass - The imported class object referred to by the python-class
      attribute. Should be an instance of L{Page} but can be anything that
      implements C{__call__(request, mapping)}.
    """
    self.id = id
    self.pythonClass = pythonClass
  def createInstance(self):
    """Factory creation for the L{Page} instance."""
    return self.pythonClass()

class ActionForward(PyWebMvcObject):
  """Generic forwarding base class that allows the L{Action} classes to
  abstractly send the user to another "place" without knowing what implements
  that "place"."""
  def __init__(self,requestHandler,mapping=None,redirect=False):
    """Constructor takes the following parameters:
    - C{requestHandler} - a callable that accepts a request and a mapping and
      returns another L{ActionForward} or None to indicate that handling is
      complete.
    - C{mapping} - An instance of L{ActionMapping} may be provided to indicate
      that the request is changing action mapping contexts.
    - C{redirect} - Can only be C{True} when mapping is provided or if
      L{getUrl} is overridden. Causes the server-side forwarding to complete
      and return a page that tells the browser to go to a new url (as
      indicated by the L{mapping<ActionMapping>} parameter).
    """
    self.requestHandler = requestHandler
    self.mapping = mapping
    self.redirect = redirect
  def getMapping(self):
    """Accessor for the mapping attribute"""
    return self.mapping
  def getUrl(self):
    """get the url for a redirect. Base implementation gets this from the
    mapping object, but subclasses can override this."""
    return self.mapping.getUrl()
  def __call__(self,req,mapping):
    """Passes through to the requestHandler callable.
    """
    nextForward = self.requestHandler(req,mapping)
    return nextForward

class PathForward(ActionForward):
  """A C{PathForward} maps an global forward id to an arbitrary server resource.
  A browser redirect is always performed with a C{PathForward}.  The following
  is the xml tag syntax for declaring path forwards::
  
  C{<forward>} - Must be defined within a top level C{<forwards>} element.
  A global C{<forward>} tag accepts the following attributes:
    - C{id} - The global id of this forward. Must be unique within the document.
    - C{path} - the server-relative path to the resource.
  """
  def __init__(self, id, path):
    super(PathForward, self).__init__(lambda req, mapping: None, redirect=True)
    self.id = id
    self.path = path
  def getUrl(self):
    return self.path

class LocalForward(ActionForward):
  """A local forward maps an L{ActionMapping}'s global id to a local name.
  This allows the action to indicate an "outcome" that is independent of the
  application navigational structure -- allowing the application flow to be
  reconfigured with little or no code change. The following is the xml tag
  syntax for declaring local forwards::
  
  C{<forward>} - defines a local "outcome" for the L{ActionMapping} and where to
  go when that outcome occurs. A C{<forward>} tag accepts the following
  attributes:
    - C{name} - the name of the L{forward<ActionForward>} that can be looked up
      from the L{action mapping<ActionMapping>} passed in to the
      L{action<Action>} handler.
    - C{global-forward} - the id of a L{PageMapping} or L{ActionMapping} that
      should handle the request next.
    - C{redirect} - only valid when using an id of another L{ActionMapping}.
      Will cause the browser to redirect to the next L{Action} instead of
      handling it on the server-side.
  """
  def __init__(self,configuration, globalForwardKey, redirect=False):
    """Constructor takes the following parameters:
    - C{configuration} - a reference to the application
      L{configuration<PyWebMvcConfiguration>}.
    - C{globalForwardKey} - string. the id of the global forward this local
      forward will go to.
    - C{redirect} - boolean. Whether to do a local forward or a browser
      redirect to get to the next action.
    """
    self.configuration = configuration
    self.globalForwardKey = globalForwardKey
    super(LocalForward,self).__init__( lambda req,mapping: configuration.globalForwards[globalForwardKey], redirect=redirect)
  def getUrl(self):
    """Returns the url of the mapping for the global forward id"""
    return self.configuration.globalForwards[self.globalForwardKey].mapping.getUrl()

class AppendQueryForward(ActionForward):
  """AppendQueryForward allows for the specification of an additional string
  that will be used as a GET query on the forward supplied to the
  AppendQueryForward constructor.  The AppendQueryForward always performs a
  redirect. 
  """
  def __init__(self, req, forward, urlQueryString):
    """Constructor takes the following parameters:
      - C{req} - the request object.
      - C{forward} - the original forward instance.
      - C{urlQueryString} - the query string. everything after the question
        mark.
    """
    self.origForward = forward
    self.queryString = urlQueryString
    super(AppendQueryForward,self).__init__( req, lambda req,mapping: None, True)
  def getUrl(self):
    """returns the url with the query string tacked on."""
    return self.origForward.getUrl() + "?" + self.queryString

class ExternalForward(ActionForward):
  """Redirects the user to an arbitrary URL.
  
  TODO: Add an xml configuration mechanism for defining these in the
  config file instead of in the code.
  """
  def __init__(self, requestHandler, url, mapping=None):
    self.url = url
    super(ExternalForward,self).__init__(requestHandler,mapping,True)
  def getUrl(self):
    return self.url
  def __call__(self,req,mapping):
    return None


class ActionError(PyWebMvcObject):
  """Associates an error message associated to a particular form field.
  """
  GLOBAL = "GLOBAL"
  """The C{GLOBAL} key is used to indicate that an error message is for the
  entire form instead of just one field."""
  def __init__(self, key, message, index = None):
    """constructs an L{ActionError}. Constructor Parameters:
    - key - The form field id that is associated to the error message or
      L{GLOBAL}.
    - message - the text of the error message.
    - index - integer. When the field is a list of values, indicates which of
      the list elements has the error.
    """
    self.key = key
    self.message = message
    self.index = index

class ActionErrors(PyWebMvcObject):
  """Container that holds L{ActionError}s and provides convenience methods for
  retrieving the errors by field."""
  def __init__(self):
    self.errors = []
  def __iter__(self):
    """iterator access for the all errors"""
    return self.errors.__iter__()
  def __nonzero__(self):
    """boolean context testing of the container. True when the there are some
    errors in the container."""
    return len(self.errors) != 0
  def __len__(self):
    """the number of errors in the container"""
    return len(self.errors)
  def removeAll(self):
    """remove the errors stored so far"""
    self.errors = []
  def addAll(self,errors):
    """Add the errors from another L{ActionErrors} Collection"""
    for error in errors:
      self.add(error)
  def hasError(self,key,index = None):
    """Test if an L{error<ActionError>} exists for the given key and index (if
    provided)"""
    for error in self.errors:
      if error.key == key:
        if index is None:
          return True
        elif index < 0:
          if error.index is None:
            return True
        else:
          if error.index == index:
            return True
    return False
  def add(self,error):
    """Add an L{error<ActionError>} to the container. Any number of errors can
    be added against any number of fields. They do not mask the other errors
    previously added against the same field/index.
    """
    self.errors.append(error)
  def getErrors(self,key,index = None):
    """get the L{ActionError}s for the form field id (or L{GLOBAL<ActionError.GLOBAL>}) and index.
    """
    errs = []
    for error in self.errors:
      if error.key == key:
        if index is None:
          errs.append(error)
        elif index < 0:
          if error.index is None:
            errs.append(error)
        else:
          if error.index == index:
            errs.append(error)
    return errs

class Action(PyWebMvcObject):
  """Action base class. Each action must have a zero-argument constructor and
  implement a L{__call__} method with the same signature. Customization of
  actions occurs at mapping time via L{attributes<ActionMapping>}.
  """
  def redirect(self, req, mapping, id,params=None):
    """utility function for forcing a redirect"""
    fwd = ActionForward(None, mapping[id], True)
    if params:
      query = htmlutil.getParameterString(params)
      fwd = AppendQueryForward(req,fwd,query)
    return fwd
  def __init__(self):
    pass
  def __call__(self, req, mapping):
    """invoke the action. Parameters:
      - C{req} - The request object
      - C{mapping} - The L{ActionMapping} object.

    returns an instance of L{ActionForward}.
    """
    return None

class DispatchAction(PyWebMvcObject):
  """A utility base L{Action} class that uses a request parameter to determine
  the method that serves the action instead of the default L{__call__}. The
  method must have the same signature as L{__call__}. The request parameter is
  determined by a C{dispatchParameter} attribute specified in the
  L{ActionMapping}. The default value is "do". E.g. C{?do=edit} in the url
  would cause the C{edit(req,mapping)} method of the action class to be called
  in place of L{__call__}. Subclasses should not override the L{__call__}
  method.
  """
  def __init__(self):
    pass
  def getDispatchParameter(self, req, mapping):
    if mapping.hasAttribute("dispatchParameter"):
      return mapping.getAttribute("dispatchParameter")
    else:
      return "do"
  def __call__(self, req, mapping):
    param = self.getDispatchParameter(req, mapping)
    if req.form.has_key(param):
        fn = getattr(self,req.form[param])
        return fn(req,mapping)
    else:
      raise PyWebMvcException("Dispatch Parameter '%s' is missing" % (param))

class Page(PyWebMvcObject):
  """Base class for returning a response to the browser."""
  def getContentType(self,req,mapping):
    """returns a mime type for the page"""
    return "text/plain"
  def getDefaultCharset(self, req):
    return "ascii"
  def getCharset(self,req,mapping):
    """returns the charset of the request but allows the page to override it."""
    if hasattr(req,"charset") and req.charset:
      return req.charset
    else:
      return self.getDefaultCharset(req)
  def getHeaders(self,req, mapping):
    """returns the http response headers for the page as a list of tuples:
      C{[ (name, value), ... ]}"""
    return [
            ("Cache-Control", "no-cache"),
            ("Pragma", "no-cache"),
           ]
  def render(self, req, mapping):
    """returns the content of the page"""
    return ""
  def __call__(self,req, mapping):
    """does the mundane mod_python integration for sending a well-formed
    response."""
    response = self.render(req, mapping)
    req.content_type = "%s; charset=%s" % (self.getContentType(req,mapping),
                                           self.getCharset(req,mapping))
    responseLength = len(response)
    req.set_content_length(responseLength)
    for header in self.getHeaders(req, mapping):
      req.headers_out[header[0]] = header[1]
    req.send_http_header()
    try:
      req.write(response)
    except:
      ###Don't raise exception if the client has closed the connection
      pass
    return None

class XMLPage(Page):
  def getContentType(self, req, mapping):
    return "text/xml"
  def getCharset(self,req,mapping):
    """overrides the L{Page} charset to provide the correct charset for
    xml content"""
    return "utf-8"
  def getProlog(self,req, mapping):
    text = """<?xml version="1.0" """
    encoding = self.getCharset(req,mapping)
    if encoding:
      text += """ encoding="%s" """ % (encoding)
    text +=  """ ?>\n"""
    return text
  def getRootElement(self, req, mapping):
    """ returns the entire root element including its contents """
    raise NotYetImplemented()
  def render(self,req, mapping):
    """puts the whole page together in the correct order. This is not usually
    overridden"""
    xml = "%s%s" % ( self.getProlog(req,mapping),
                     self.getRootElement(req, mapping))
    return xml
  
  
class HtmlPage(Page):
  """Further enhances L{Page} to be specifically an HTML response."""
  def getStylesheets(self,req,mapping):
    """returns a list of server-absolute urls pointing the the stylesheets
    for the html page"""
    return []
  def getContentType(self,req,mapping):
    """overrides the L{Page} content type to provide the correct mime type for
    html content"""
    return "text/html"
  def getDefaultCharset(self, req):
    return "utf-8"
  def getScripts(self,req,mapping):
    """returns a list of server-absolute urls pointing the the scripts
    for the html page.
    Uses C{pyWebMvcJsFileURL} (optional) - The full path to the pyWebMVC javascript file
    """
    options = req.get_options()
    if options and options.has_key("pyWebMvcJsFileURL"):
      return [options["pyWebMvcJsFileURL"]]
    return ['/pywebmvc-data/script/pywebmvc.js']
  def getPreamble(self,req, mapping):
    """returns the html preamble. Uses C{HTML 4.0 Transitional} by default.
    Override this method to change the doctype."""
    return '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">\n'
  def getPageStart(self,req, mapping):
    """returns C{<html>}"""
    return "<html>"
  def getPageEnd(self,req,mapping):
    """returns C{</html>}"""
    return "</html>"
  def getTitle(self,req, mapping):
    """returns the title of the page. Does not include the C{<title>} tag."""
    return ""
  def isHttps(self, req):
    """Utility function for determining if the server is using http or https.
    For efficiency, an application that is always HTTPS or HTTP can override
    this to return True or False accordingly.
    """
    req.add_common_vars()
    return req.subprocess_env.has_key('HTTPS') and \
           req.subprocess_env['HTTPS'] == 'on'
  def getBase(self, req, mapping):
    """returns the url to be used as the base for the page according to the
    action mapping context. This will ensure that pages work correctly when
    server-side forwards are used. not usually overridden."""
    from formutils import href
    from mod_python import apache as mod_apache
    try:
      host = req.hostname
      if req.parsed_uri and req.parsed_uri[mod_apache.URI_PORT]:
        host += ":"+req.parsed_uri[mod_apache.URI_PORT]
      return "%s://%s%s" % (
      ("http","https")[self.isHttps(req)],
      host,
      href(req, mapping.id)
      )
    except:
      return None
  def getHeaderStart(self,req,mapping):
    """Construct the html header using the title, stylesheets, scripts, and
    base values returned. Not usually overridden but if it is, it is a
    best-practice to call super and then add additional head content.
    """
    headerStart = "<head><title>%s</title>" % (self.getTitle(req,mapping))
    for stylesheetUrl in self.getStylesheets(req,mapping):
      headerStart += '<link rel="stylesheet" type="text/css" href="%s">' % (stylesheetUrl)
    for scriptUrl in self.getScripts(req,mapping):
      headerStart += '<script type="text/javascript" src="%s"></script>' % (scriptUrl)
    base = self.getBase(req, mapping)
    if base:
      headerStart += '<base href="%s">' % base
    return headerStart
  def getHeaderEnd(self,req, mapping):
    """returns C{</head>}"""
    return "</head>"
  def getBodyStart(self,req,mapping):
    """renders the body start. often overridden."""
    return "<body>"
  def getBodyEnd(self,req,mapping):
    """renders the body end. often overridden."""
    return "</body>"
  def render(self,req, mapping):
    """puts the whole page together in the correct order. This is not usually
    overridden"""
    page = "%s%s%s%s%s%s%s" % (
                                self.getPreamble(req,mapping),
                                self.getPageStart(req,mapping),
                                self.getHeaderStart(req,mapping),
                                self.getHeaderEnd(req,mapping),
                                self.getBodyStart(req,mapping),
                                self.getBodyEnd(req,mapping),
                                self.getPageEnd(req,mapping)
                              )
    return page.encode(self.getCharset(req,mapping))

class PyWebMvcConfiguration(PyWebMvcObject):
  """Stores the application configuration as a singleton after it is parsed
  from the configuration xml file.
  """
  def __init__(self,prefix,extension):
    """C{prefix} and C{extension} are read from the apache configuration::

    PythonOption pyWebMvcPrefix /myapp
    PythonOption pyWebMvcExtension pwm
    """
    from render.factory import pyWebMvcDefaultRendererFactory
    from metadata import FieldMetadata, FormMetadata, MetadataGroup
    self.prefix = prefix
    self.extension = extension
    self.typeMetadata = {}
    self.rendererFactories = {}
    self.defaultRendererFactory = pyWebMvcDefaultRendererFactory
    self.formMetadata = {}
    self.pageMappings = {}
    self.actionMappings = {}
    self.globalForwards = {}
    self.errorHandlers = []
    self.metadataClasses = {
      "field" : FieldMetadata,
      "form" : FormMetadata,
      "fieldgroup" : MetadataGroup,
    }
  def addRendererFactory(self,id,factory):
    """Adds a L{RendererFactory<pywebmvc.framework.render.factory.RendererFactory>} with the
    specified id."""
    self.rendererFactories[id] = factory
  def getRendererFactory(self,id):
    """Gets a L{RendererFactory<pywebmvc.framework.render.factory.RendererFactory>} with the
    specified id."""
    return self.rendererFactories[id]
  def addErrorHandler(self,handler):
    """Adds an L{ErrorHandler}."""
    self.errorHandlers.append(handler)
  def getErrorHandlers(self):
    """Gets all of the L{ErrorHandlers<ErrorHandler>}."""
    return self.errorHandlers
  def getDefaultRendererFactory(self):
    """Gets the default L{RendererFactory<pywebmvc.framework.render.factory.RendererFactory>}."""
    return self.defaultRendererFactory
  def setDefaultRendererFactory(self, factory):
    """Sets the default L{RendererFactory<pywebmvc.framework.render.factory.RendererFactory>}."""
    self.defaultRendererFactory = factory
  def addGlobalForward(self,globalId,forward):
    """Adds a L{forward<ActionForward>} with the specified globalId.
    Global forwards are created automatically for each L{page<PageMapping>} and
    L{action<ActionMapping>} mapping."""
    if self.globalForwards.has_key(globalId):
      raise PyWebMvcInvalidConfigurationException("global forward id '%s' already exists" % (globalId))
    else:
      self.globalForwards[globalId] = forward
  def addTypeMetadata(self,type):
    """Adds a L{TypeMetadata<metadata.TypeMetadata>} to the application."""
    self.typeMetadata[type.id] = type
  def getTypeMetadata(self, id):
    """Gets the L{TypeMetadata<metadata.TypeMetadata>} with the specified id."""
    return self.typeMetadata[id]
  def addFormMetadata(self,form):
    """Adds a L{FormMetadata<metadata.TypeMetadata>} to the application."""
    if self.formMetadata.has_key(form.id):
      raise PyWebMvcInvalidConfigurationException("form with id '%s' already exists" % (form.id,))
    self.formMetadata[form.id] = form
  def getFormMetadata(self, id):
    """Gets the L{FormMetadata<metadata.TypeMetadata>} with the specified id."""
    return self.formMetadata[id]
  def addPageMapping(self,pageMapping):
    """Adds a L{PageMapping} to the application."""
    self.pageMappings[pageMapping.id] = pageMapping
    self.addGlobalForward(pageMapping.id,ActionForward(pageMapping.createInstance()))
  def getPageMapping(self, id):
    """Gets the L{PageMapping} with the specified id."""
    return self.pageMappings[id]
  def addActionMapping(self,actionMapping):
    """Adds an L{ActionMapping} to the application."""
    try:
      mapping = self.getActionMappingByPath(actionMapping.path)
      raise PyWebMvcInvalidConfigurationException("path '%s' on action '%s' is already defined for mapping '%s'" % (mapping.path, actionMapping.id, mapping.id))
    except ActionNotFoundException:
      pass
    self.actionMappings[actionMapping.id] = actionMapping
    self.addGlobalForward(actionMapping.id,ActionForward(actionMapping.createInstance(), actionMapping))
  def getActionMappings(self):
    """Returns a list of all the L{ActionMappings<ActionMapping>}
    in the application."""
    return self.actionMappings.values()
  def getActionMapping(self,id):
    """Gets the L{ActionMapping} with the specified id."""
    return self.actionMappings[id]
  def getActionMappingsByAttribute(self,name,value):
    """Gets all of the L{ActionMappings<ActionMapping>} with 
    an attribute C{name} having C{value}."""
    mappings = []
    for actionMapping in self.actionMappings.values():
      if actionMapping.hasAttribute(name):
        if actionMapping.getAttribute(name) == value:
          mappings.append(actionMapping)
    return mappings
  def getActionMappingByPath(self,path):
    """Gets the L{ActionMapping} having the specified C{path} (prefix
    and extension removed)."""
    for actionMapping in self.actionMappings.values():
      if actionMapping.path == path:
        return actionMapping
    raise ActionNotFoundException(path)
  def setMetadataClass(self, type, constructor):
    assert type in ("field", "fieldgroup", "form")
    self.metadataClasses[type] = constructor
