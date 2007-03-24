#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""Reads the XML configuration file and parses it into the PyWebMVC object
model."""
import types
from copy import copy
from xml.dom.minidom import parse
from xml.dom import Node

from core import *
from metadata import *
from validate import *
from resourcebundle import BundleManager, ResourceBundle
from util import TabIndexTable

pyWebMvcConfig = None
def getPyWebMvcConfig(req):
  """returns the singleton instance of the L{application configuration<core.PyWebMvcConfiguration>}."""
  global pyWebMvcConfig
  if not pyWebMvcConfig:
    pyWebMvcConfig = readConfig(req)
  return pyWebMvcConfig

class Initializer(object):
  def __init__(self,configFileName, prefix = None,extension = None):
    self.configFileName = configFileName
    self.prefix = prefix
    self.extension = extension
  def initialize(self):
    global pyWebMvcConfig
    pyWebMvcConfig = readConfigFromFile(self.configFileName,
                                        self.prefix,
                                        self.extension)

def readConfig(req):
  """Accepts a C{mod_python} request object and uses the following options to create the application L{configuration<pywebmvc.framework.core.PyWebMvcConfiguration>}:
    - C{pyWebMvcConfig} - The full path to the configuration xml file. E.g.
      /home/foo/myapp/config.xml
    - C{pyWebMvcPrefix} - The application context for this application.
      Defaults to "/", If overridden, should begin with a "/" but not end with
      one.
    - C{pyWebMvcExtension} - If provided, add C{"."+extension} to each action
      path. If omitted, no extension will be used.
  """
  options = req.get_options()
  file = options["pyWebMvcConfig"]
  prefix = None
  extension = None
  if options.has_key("pyWebMvcPrefix"):
    prefix = options["pyWebMvcPrefix"]
  if options.has_key("pyWebMvcExtension"):
    extension = options["pyWebMvcExtension"]
  return readConfigFromFile(file,prefix,extension)

def readConfigFromFile(file,prefix,extension):
  """Returns a L{configuration<pywebmvc.framework.core.PyWebMvcConfiguration>}
  object having been set up according to the provided C{file}, C{prefix} and
  C{extension}. All arguments are strings, the file parameter is a path to the
  xml configuration file.
  """
  config = PyWebMvcConfiguration(prefix,extension)
  document = parse(file)

  resourcesElements = document.getElementsByTagName("resources")
  assert len(resourcesElements) <= 1
  if resourcesElements:
    readResources(resourcesElements[0], config)
  else:
    config.bundleManager = BundleManager()

  typesElements = document.getElementsByTagName("types")
  assert len(typesElements) == 1
  readTypes(typesElements[0], config)
  
  renderersElements = document.getElementsByTagName("renderers")
  assert len(renderersElements) <= 1
  if len(renderersElements) == 1:
    readRendererFactories(renderersElements[0], config)
  
  formsElements = document.getElementsByTagName("forms")
  assert len(formsElements) == 1
  metadataElements = childrenByTagName(formsElements[0], "metadata")
  for metadataElement in metadataElements:
    config.setMetadataClass(metadataElement.getAttribute("type"),
                            getPythonClass(metadataElement))
  readForms(formsElements[0], config)

  pagesElements = document.getElementsByTagName("pages")
  assert len(pagesElements) == 1
  readPageMappings(pagesElements[0], config)

  forwardsElements = document.getElementsByTagName("forwards")
  assert len(forwardsElements) <= 1
  if len(forwardsElements) > 0:
    readGlobalForwards(forwardsElements[0], config)

  actionsElements = document.getElementsByTagName("actions")
  assert len(actionsElements) == 1
  readActionMappings(actionsElements[0], config)

  errorHandlersElements = document.getElementsByTagName("error-handlers")
  if errorHandlersElements:
    assert len(errorHandlersElements) == 1
    readErrorHandlers(errorHandlersElements[0], config)

  document.unlink()
  return config

def readTypes(typesElement,config):
  typeElements = childrenByTagName(typesElement, "type")
  for typeElement in typeElements:
    id = typeElement.getAttribute("id")
    input = typeElement.getAttribute("input")
    maxlengthStr = typeElement.getAttribute("max-length")
    if maxlengthStr:
      maxlength = int(maxlengthStr)
    else:
      maxlength = 0
    typeValidation = getValidationFunction(typeElement)
    type = TypeMetadata(id, input, maxlength, typeValidation)
    config.addTypeMetadata(type)

def readRendererFactories(formsElement, config):
  factoryElements = childrenByTagName(formsElement, "factory")
  for element in factoryElements:
    id = element.getAttribute("id")
    isDefault = element.getAttribute("default") == "true"
    factoryClass = getPythonClass(element)
    factory = factoryClass()
    config.addRendererFactory(id,factory)
    if isDefault:
      config.setDefaultRendererFactory(factory)

def readForms(formsElement, config):
  formElements = childrenByTagName(formsElement, "form")
  for element in formElements:
    formMetadata = unmarshallForm(element, config)
    config.addFormMetadata(formMetadata)

def readPageMappings(pagesElement, config):
  pageElements = childrenByTagName(pagesElement, "page")
  for pageElement in pageElements:
    id = pageElement.getAttribute("id")
    pythonClass = getPythonClass(pageElement)
    assert id
    assert pythonClass
    config.addPageMapping(PageMapping(id, pythonClass))

def readGlobalForwards(forwardsElement, config):
  forwardElements = childrenByTagName(forwardsElement, "forward")
  for forwardElement in forwardElements:
    id = forwardElement.getAttribute("id")
    path = forwardElement.getAttribute("path")
    assert id
    assert path
    config.addGlobalForward(id,PathForward(id, path))

def readActionMappings(actionsElement, config):
  actionElements = childrenByTagName(actionsElement, "action")
  for actionElement in actionElements:
    id = actionElement.getAttribute("id")
    pythonClass = getPythonClass(actionElement)
    path = actionElement.getAttribute("path")
    formMetadata = actionElement.getAttribute("form")
    if formMetadata:
      formMetadata = config.getFormMetadata(formMetadata)
    else:
      formMetadata = None
    rendererFactory = actionElement.getAttribute("renderer-factory")
    if rendererFactory:
      rendererFactory = config.getRendererFactory(rendererFactory)
    else:
      rendererFactory = config.getDefaultRendererFactory()
    assert id
    assert pythonClass
    ##TODO allow global mapping override via the config
    mappingClass = getPythonClass(actionElement, "mapping-class", ActionMapping)
    mapping = mappingClass(id, path, pythonClass, config, formMetadata, rendererFactory)
    forwardElements = childrenByTagName(actionElement, "forward")
    for forwardElement in forwardElements:
      name = forwardElement.getAttribute("name")
      globalForwardKey = forwardElement.getAttribute("global-forward")
      redirect = (forwardElement.getAttribute("redirect") == "true")
      mapping.addLocalForward(name,
        LocalForward(config, globalForwardKey, redirect))
    attributeElements = childrenByTagName(actionElement, "attribute")
    for attributeElement in attributeElements:
      mapping.setAttribute(attributeElement.getAttribute("name"),
                           attributeElement.getAttribute("value"))
    config.addActionMapping(mapping)

def readErrorHandlers(element, config):
  errorHandlerElements = element.getElementsByTagName("error-handler")
  for element in errorHandlerElements:
    if element.hasAttribute("python-class"):
      constructor = getPythonClass(element, "python-class")
    else:
      constructor = ErrorHandler
    config.addErrorHandler(
      constructor(getPythonClass(element, "exception-class"),
                  element.getAttribute("forward")))
    

def parseImport(value):
  if value.find("::") > 0:
    return value.split("::",1)
  else:
    return (None, value)

def getPythonClass(element,attrName = "python-class",defaultValue=None):
  if element.hasAttribute(attrName):
    (module, klass) = parseImport(element.getAttribute(attrName))
    return importObject(module, klass)
  return defaultValue

def importObject(moduleName, functionName):
  if moduleName:
    #str:ok
    module = __import__(moduleName,{},{},[str(functionName)])
    return getattr(module,functionName)
  else:
    return eval(functionName)

def getValidationFunction(element):
  functions = []
  validationElements = childrenByTagName(element, "validation")
  for validationElement in validationElements:
    type = validationElement.getAttribute("type")
    errorMsgKey = validationElement.getAttribute("error-message")
    if type == "enumeration":
      valueTags = validationElement.getElementsByTagName("value")
      values = []
      for valueTag in valueTags:
        if (valueTag.firstChild and
            valueTag.firstChild.nodeType == Node.TEXT_NODE):
          value = {}
          value["value"] = valueTag.firstChild.nodeValue
          value["label"] = valueTag.getAttribute("label")
          values.append(value)
      functions.append(createEnumValidator(values, errorMsgKey))
    elif type == "enumgenerator":
      valueTags = validationElement.getElementsByTagName("value")
      if len(valueTags) == 1 and valueTags[0].firstChild:
        functionStr = valueTags[0].firstChild.nodeValue
        (module, funcName) = parseImport(functionStr)
        functions.append(createEnumGeneratorValidator(importObject(module, funcName), errorMsgKey))
      else:
        raise PyWebMvcInvalidConfigurationException("enumgenerator <validation> tags should have exactly one <value>")
    elif type == "regex":
      valueTags = validationElement.getElementsByTagName("value")
      if len(valueTags) == 1 and valueTags[0].firstChild:
        regexStr = valueTags[0].firstChild.nodeValue
        functions.append(createRegexValidator(regexStr, errorMsgKey))
      else:
        raise PyWebMvcInvalidConfigurationException, "regex <validation> tags should have exactly one <value>"
    elif type == "function":
      valueTags = validationElement.getElementsByTagName("value")
      if len(valueTags) == 1 and valueTags[0].firstChild:
        functionStr = valueTags[0].firstChild.nodeValue
        (module, funcName) = parseImport(functionStr)
        functions.append(importObject(module, funcName))
      else:
        raise PyWebMvcInvalidConfigurationException, "function <validation> tags should have exactly one <value>"
    else:
      raise PyWebMvcInvalidConfigurationException, "validation type '%s' is not supported" % (type)
  if len(functions) == 1:
    return functions[0]
  else:
    return createMultiValidator(*functions)

def addRenderers(metadataElement, md):
  rendererElements = childrenByTagName(metadataElement, "renderer")
  for rendererElement in rendererElements:
    type = rendererElement.getAttribute("type")
    rendererClass = getPythonClass(rendererElement)
    renderer = rendererClass()
    md.setRenderer(type, renderer)
def addAttributes(metadataElement, md):
  attributeElements = childrenByTagName(metadataElement, "attribute")
  for attributeElement in attributeElements:
    name = attributeElement.getAttribute("name")
    value = attributeElement.getAttribute("value")
    md.setAttribute(name, value)

def unmarshallGroupChildren(groupElement, metadataGroup, config, tabIndexTable):
  metadataElements = childrenByTagName(groupElement, "metadata")
  for metadataElement in metadataElements:
    assert metadataElement.getAttribute("type") in ("field", "fieldgroup")
    metadataGroup.setMetadataClass(metadataElement.getAttribute("type"),
                                   getPythonClass(metadataElement))
  children = childrenByTagNames(groupElement, ["field", "fieldgroup"])
  for child in children:
    if child.tagName == "field":
      metadataGroup.addMetadata(unmarshallField(child, config, metadataGroup, tabIndexTable))
    elif child.tagName == "fieldgroup":
      metadataGroup.addMetadata(unmarshallFieldGroup(child, config, metadataGroup, tabIndexTable))
  addAttributes(groupElement,metadataGroup)
  addRenderers(groupElement,metadataGroup)

def unmarshallFieldGroup(element, config, parent, tabIndexTable):
  name = element.getAttribute("name")
  property = element.getAttribute("property")
  pythonClass = getPythonClass(element)
  metadataClass = getMetadataClass(config, "fieldgroup", parent, element)
  required = (element.getAttribute("required") == "true")
  if element.hasAttribute("display-required"):
    displayRequired = (element.getAttribute("display-required") == "true")
  else:
    displayRequired = None
  requiredErrorMessage = element.getAttribute("required-error-msg")
  label = element.getAttribute("label")
  list = (element.getAttribute("list") == "true")
  instruction = element.getAttribute("instruction")
  metadataGroup = metadataClass(name, property, pythonClass, required, displayRequired, requiredErrorMessage, label, list, instruction=instruction)
  unmarshallGroupChildren(element, metadataGroup, config, tabIndexTable)
  return metadataGroup

def childrenByTagName(parentNode, tagName):
  return childrenByTagNames(parentNode, [tagName])

def childrenByTagNames(parentNode, tagNames):
  children = []
  for child in parentNode.childNodes:
    if (child.nodeType == Node.ELEMENT_NODE and
        child.tagName in tagNames):
      children.append(child)
  return children

def unmarshallField(fieldElement, config, parent, tabIndexTable):
  name = fieldElement.getAttribute("name")
  tabIndexTable.add(name)
  property = fieldElement.getAttribute("property")
  required = (fieldElement.getAttribute("required") == "true")
  if fieldElement.hasAttribute("display-required"):
    displayRequired = (fieldElement.getAttribute("display-required") == "true")
  else:
    displayRequired = None
  requiredErrorMessage = fieldElement.getAttribute("required-error-msg")
  type = config.getTypeMetadata(fieldElement.getAttribute("type"))
  label = fieldElement.getAttribute("label")
  hidden = (fieldElement.getAttribute("hidden") == "true")
  cssClass = fieldElement.getAttribute("class")
  maxlengthStr = fieldElement.getAttribute("max-length")
  instruction = fieldElement.getAttribute("instruction")
  defaultValue = fieldElement.getAttribute("default-value")
  list = (fieldElement.getAttribute("list") == "true")
  pythonClass = getPythonClass(fieldElement)
  metadataClass = getMetadataClass(config,"field", parent, fieldElement)
  if maxlengthStr:
    maxlength = int(maxlengthStr)
  else:
    maxlength = 0
  fieldValidation = getValidationFunction(fieldElement)
  fmd = metadataClass(name, property, required, displayRequired, requiredErrorMessage, type,
    label, cssClass, hidden, maxlength, fieldValidation, pythonClass,
    instruction, list, defaultValue)
  addAttributes(fieldElement, fmd)
  addRenderers(fieldElement,fmd)
  return fmd

def getMetadataClass(config, type, groupMetadata, element):
  if groupMetadata and groupMetadata.metadataClasses.has_key(type):
    defaultClass = groupMetadata.metadataClasses[type]
  else:
    defaultClass = config.metadataClasses[type]
  return getPythonClass(element, "metadata-class", defaultClass)

def unmarshallForm(element, config):
  formName = element.getAttribute("id")
  method = element.getAttribute("method")
  type = element.getAttribute("type")
  listVal = element.getAttribute("list") == "true"

  pythonClass = getPythonClass(element)
  metadataClass = getMetadataClass(config, "form", None, element)
  formValidation = getValidationFunction(element)
  tabIndexTable = TabIndexTable()
  formMetadata = metadataClass(formName, pythonClass, tabIndexTable, formValidation, method=method, type=type, list=listVal)
  unmarshallGroupChildren(element, formMetadata, config, tabIndexTable)
  if element.hasAttribute("focus"):
    formMetadata.setFocus(element.getAttribute("focus"))
  return formMetadata

def readResources(element, config):
  resourceBundleElements = element.getElementsByTagName("resource-bundle")
  firstLocale = None
  defaultLocale = None
  bundleManager = BundleManager()
  for resourceBundleElement in resourceBundleElements:
    locale = resourceBundleElement.getAttribute("locale")
    if resourceBundleElement.hasAttribute("default"):
      default = resourceBundleElement.getAttribute("default").lower()
    else:
      default = "false"
    if not firstLocale:
      firstLocale = locale
    if default in ("true", "yes", "on", "1"):
      if defaultLocale:
        raise PyWebMvcInvalidConfigurationException("Multiple default locales")
      defaultLocale = locale
    bundle = ResourceBundle()
    #XXX should we process the reading of files and property tags so that
    #XXX overridding happens in document order?
    propertiesElements = resourceBundleElement.getElementsByTagName("properties")
    for propertiesElement in propertiesElements:
      bundle.addPropertiesFile(propertiesElement.getAttribute("path"))
    propertyElements = resourceBundleElement.getElementsByTagName("property")
    for propertyElement in propertyElements:
      key = propertyElement.getAttribute("key")
      value = propertyElement.getAttribute("value")
      bundle[key] = value
    bundleManager.registerBundle(locale, bundle)
  if not defaultLocale:
    defaultLocale = firstLocale
  if defaultLocale:
    bundleManager.setDefaultLocale(defaultLocale)
  config.bundleManager = bundleManager

