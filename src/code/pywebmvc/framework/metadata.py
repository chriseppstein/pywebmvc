#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

"""Metadata about forms which allows for simple transfer to and from model objects (L{Entities<Entity>}) to a html form (key/value pairs) in the view layer."""

import re, weakref, types
from core import ActionErrors, PyWebMvcException, PyWebMvcInvalidConfigurationException
from util import PyWebMvcObject
from weakref import ReferenceType

DISPLAY_READONLY = "readonly"
DISPLAY_NORMAL = "normal"
DISPLAY_HIDDEN = "hidden"

class WebBoolean(PyWebMvcObject):
  """A boolean object which understands the standard boolean textual
  representations. The following values are interpreted (case-insensitive) as
  C{True}; All other values are C{False}:
    - on
    - true
    - yes
    - 1
    - checked
  """
  def __init__(self,b=False):
    """A WebBoolean can be constructed from another WebBoolean,
    a python boolean, a string, otherwise use c{bool(b)} as the value."""
    if isinstance(b, WebBoolean):
      self.value = b.value
    elif isinstance(b,types.BooleanType):
      self.value = b
    elif isinstance(b,types.StringTypes):
      self.value = (b.lower() in ("on", "true", "yes", "1", "checked"))
    else:
      self.value = bool(b)
  def __eq__(self,other):
    """True if the boolean value of C{other} and the boolean value of this
    WebBoolean are the same."""
    return self.value == bool(other)
  def __cmp__(self,other):
    return cmp(self.value,other.value)
  def __str__(self):
    """Output as a string using C{"on"} for C{True} and C{"off"} for
    C{False}."""
    if self.value:
      return "on"
    else:
      return "off"
  def __nonzero__(self):
    return self.value
  def __repr__(self):
    return "WebBoolean(%s)" % (repr(self.value))

class Entity(PyWebMvcObject):
  """Base class for model objects which are to be used with the PyWebMVC
  metadata transfer functions."""
  def getProperties(self):
    return self.__dict__.keys()

def transferToEntityOld(form, metadata, property = None, req = None):
  """Construct a model-layer object instance from the values stored in
  L{form<formutils.FieldStorage>} as governed by the form
  L{metadata<FormMetadata>}. C{property} should not be passed in the top level
  call -- it is used when recursing down object hierarchies."""
  if isinstance(metadata, FieldMetadata):
    if metadata.list:
      if form.has_key(metadata.id):
        if isinstance(form[metadata.id], types.ListType):
          rv = []
          for v in form[metadata.id]:
            if metadata.pythonClass:
              rv.append(metadata.pythonClass(v))
            else:
              rv.append(v)
          return rv
        else:
          if metadata.pythonClass:
            return [metadata.pythonClass(form[metadata.id])]
          else:
            return [form[metadata.id]]
      else:
        return []
    elif metadata.pythonClass:
      if form.has_key(metadata.id) and form[metadata.id]:
        v = form[metadata.id]
        if isinstance(v, types.ListType):
          return [ metadata.pythonClass(vi) for vi in v ]
        else:
          return metadata.pythonClass(v)
      else:
        try:
          return metadata.pythonClass()
        except:
          return None
    else:
      if form.has_key(metadata.id):
        return form[metadata.id]
      else:
        return None
  elif metadata.pythonClass:
    if metadata.list:
      value = []
      propArrays = {}
      num = 0
      for subProp in metadata.getProperties():
        subValue = transferToEntity(form,
          metadata.getMetadataByProperty(subProp), None, req)
        if isinstance(subValue, types.ListType):
          num = len(subValue)
          propArrays[subProp] = subValue
        elif subValue:
          num = 1
          propArrays[subProp] = [subValue]
      for i in range(num):
        v = metadata.pythonClass()
        for subProp in propArrays.keys():
          exec("v.%s = propArrays[subProp][i]" % (subProp))
        value.append(v)
      return value
    else:
      value = metadata.pythonClass()
      for subProp in metadata.getProperties():
        subValue = transferToEntity(form,
          metadata.getMetadataByProperty(subProp), None, req)
        exec("value.%s = subValue" % (subProp))
      return value
  else:
    raise ValueError

def transferToEntity(form, metadata, property = None, req = None):
  pool = makeInitialPool(form)
  doTransferToEntity(metadata, pool)
  return pool[metadata.id].getValue()

def makeInitialPool(form):
  return dict(map(lambda x: (x, PoolItem.create(makeList(form[x]), False)), form.keys()))

def makeList(value):
  return isinstance(value, types.ListType) and value or [value]

def doTransferToEntity(node, pool):
  if not isLeaf(node):
    for key in node.keys():
      doTransferToEntity(node.getMetadata(key), pool)
  poolEntry = isLeaf(node) and makeLeafEntry(node, pool) or makeParentEntry(node, pool) 
  pool[node.id] = poolEntry

def isLeaf(node):
  return isinstance(node, FieldMetadata)

def makeLeafEntry(node, pool):
  if not pool.has_key(node.id):
    return PoolItem.create([], node.list)
  poolElem = pool[node.id]
  if not node.pythonClass:
    newComponents = poolElem.getComponents()
  else:
    newComponents = map(lambda x: makeComponent(x, node), poolElem.getComponents())
  return PoolItem.create(newComponents, node.list)

def makeComponent(oldComponent, node):
  if oldComponent:
    return node.pythonClass(oldComponent)
  try:
    return node.pythonClass()
  except:
    return None
  
def makeParentEntry(node, pool):
  poolItemList = [pool[x] for x in node.keys()]
  numToCreate = max(map(lambda x: x.getCount(), poolItemList))
  resultComponents = []
  for i in range(numToCreate):
    value = node.pythonClass()
    for key in node.keys():
      if node.getMetadata(key).property:
        setattr(value, node.getMetadata(key).property, pool[key].getComponent(i))
    resultComponents.append(value)
  return PoolItem.create(resultComponents, node.list)
      
class PoolItem:
  def create(components, isList):
    return isList and ListPoolItem(components) or StandardPoolItem(components)
  create = staticmethod(create)
  def getCount(self):
    return len(self.getComponents())

class StandardPoolItem(PoolItem):
  def __init__(self, components):
    self.components = components
  def getComponent(self, idx):
    if idx >= len(self.components):
      return None
    return self.components[idx]
  def getComponents(self):
    return self.components
  def getValue(self):
    return len(self.components) == 1 and self.components[0] or self.components
  def __repr__(self):
    return """ StandardPoolItem(%s) """ % (repr(self.components))

class ListPoolItem(PoolItem):
  def __init__(self, components):
    self.components = components
  def getComponent(self, idx):
    if idx == 0:
      return self.components
    raise IndexError
  def getComponents(self):
    return [self.components] 
  def getValue(self):
    return self.components
  def __repr__(self):
    return """ ListPoolItem(%s) """ % (repr(self.components))
  

def transferToForm(value, form, metadata, property = None):
  """Transfer the L{value<Entity>} to the L{form<formutils.FieldStorage>}
  as described in the L{metadata<FormMetadata>}. C{property} should not be
  passed in the top level call -- it is used when recursing down object
  hierarchies.
  """
  if property is None:
    if isinstance(value, Entity):
      for propName in value.getProperties():
        prop = getattr(value, propName)
        transferToForm(prop, form, metadata, propName)
    elif isinstance(metadata, FieldMetadata):
      if form.has_key(metadata.id):
        oldVal = form[metadata.id]
        if isinstance(oldVal, types.ListType):
          oldVal.append(unicode(value))
        else:
          oldVal = [oldVal, unicode(value)]
        form[metadata.id] = oldVal
      else:
        form[metadata.id] = unicode(value)
    else:
      raise ValueError, "property or entity required for transfer"
  elif isinstance(value, types.ListType): #lists of lists will fail here.
    md = None
    if metadata.hasProperty(property):
      md = metadata.getMetadataByProperty(property)
      if md.list:
        for item in value:
          transferToForm(item, form, md, None)
      else:
        form[md.id] = map(unicode,value)
  elif isinstance(value, Entity):
    for propName in value.getProperties():
      prop = getattr(value, propName)
      if metadata.hasProperty(property):
        transferToForm(prop, form, metadata.getMetadataByProperty(property), propName)
      else:
        transferToForm(prop, form, metadata, "%s.%s" % (property, propName))
  elif metadata.hasProperty(property):
    if not (value is None):
      id = metadata.getMetadataByProperty(property).id
      if form.has_key(id) and isList(metadata):
        if isinstance(form[id], types.ListType):
          form[id] = form[id] + [unicode(value)]
        else:
          form[id] = [form[id],unicode(value)]
      else:
        form[id] = unicode(value)

def isList(metadata):
  """Determines if the current form key is multi-valued by seeing if it or any
  of its parents groups are a list."""
  while metadata:
    if metadata.list:
      return True
    else:
      metadata = metadata.parent
  return False
    
class MetadataBase(PyWebMvcObject):
  """Base class providing common structure and functionality to different types
  of metadata."""
  def __init__(self, id, property, pythonClass = None, required=False,
               displayRequired = None, requiredErrorMessage=None,
               label = None, list = False, validate = None, instruction=None):
    """Construct accepts the following parameters:
    - id - The identifier for this metadata.
    - property - the model property to which this metadata applies (or C{None}).
    - pythonClass - The model-layer python class which is used for this
      metadata or C{None}. Should be class object.
    - required - Whether this property is required to be provided by the user.
    - displayRequired - This will display the field as required or not
      irrespective of the required attribute. When set to None, this
      will follow the required attribute.
    - requiredErrorMessage - The error message resource bundle key which should
      be used when the required property is not provided.
    - label - The resource bundle key to be used for the field label.
    - list - Boolean indicating whether this property is a list.
    - validate - The callable that will validate the user input.
    """
    if not validate:
      def defValidator(*args, **kwargs):
        return ActionErrors()
      validate = defValidator
    self.id = id
    self.property = property
    self.pythonClass = pythonClass
    self.required = required
    self.dispRequired = displayRequired
    self.requiredErrorMessage = requiredErrorMessage
    self.label = label
    self.list = list
    self.validate = validate
    self.parent = None
    self.renderers = {}
    self.attributes = {}
    self.instruction = instruction
  def getInstruction(self, req, mapping):
    return self.instruction
  def isRequired(self, req, mapping):
    return self.required
  def displayRequired(self, req, mapping):
    if self.dispRequired is None:
      return self.isRequired(req,mapping)
    else:
      return self.dispRequired
  def getRequiredErrorMessage(self, req):
    return self.requiredErrorMessage
  def getLabel(self, req, mapping):
    return self.label
  def setParent(self, parent):
    """set the metadata parent for this metadata."""
    self.parent = weakref.proxy(parent) #avoid the referential loop
  def getForm(self):
    """get the top-level form metadata."""
    form = self
    while not (form.parent is None):
      form = form.parent
    if isinstance(form, ReferenceType):
      return form() #need to dereference the weakref
    else:
      return form
  def setAttribute(self, name, value):
    """set an attribute for this metadata"""
    self.attributes[name] = value
  def getAttribute(self, name):
    """get an attribute from this metadata with C{name}"""
    return self.attributes[name]
  def hasAttribute(self, name):
    """check if an attribute for this metadata exists with C{name}."""
    return self.attributes.has_key(name)
  def setRenderer(self, type, renderer):
    """set the renderer for C{type} in this context, overriding the default in
    the factory"""
    self.renderers[type] = renderer
  def getRenderer(self, type):
    """get the renderer for C{type} in this metadata context."""
    return self.renderers[type]
  def hasRenderer(self, type):
    """get the renderer for C{type} in this metadata context."""
    return self.renderers.has_key(type)

class FieldMetadata(MetadataBase):
  """Metadata for a single field in a form. FieldMetadata is defined in the xml
  configuration file according to the following syntax:

  C{<field>} tags define a form field within the context of a C{<form>} or
  C{<field-group>}. The C{<field>} tag accepts the following attributes:
    - C{name} - The name of the field. Required. Must be unique within the
      entire form.
    - C{type} - The id of the type defined elsewhere in the config.xml file.
    - C{property} - Optional. The property on the model layer python object
      where this field is read/written when transferring.
    - C{python-class} - Optional. The python class for this field. Defaults to
      a string. This class constructor must take a single string parameter
      which is the value.
    - C{required} - Optional. When set to true the field must be entered by the
      user or an error will result.
    - C{required-error-message} - Optional. Overrides the default message when
      the required field is missing. A resource bundle key.
    - C{label} - Optional. The message resource key used to display the name of
      the field to the user.
    - C{hidden} - Optional. When set to "true" the field should be on the page
      but not displayed to the user.
    - C{class} - Optional. The CSS class for the field.
    - C{max-length} - Optional. The maximum length for the field. Overrides the
      value provided by the type if it is smaller.
    - C{instruction} - Optional. A message resource key to give additional
      information about the field.
    - C{default-value} - Optional. If no value is present, this value will be
      used.
    - C{list} - Optional. When set to "true" this field is interpreted as a
      list of values.

  Additionally, a field can have the following child elements:
    - C{<validation>} - see the description of this element under
      L{TypeMetadata}.
    - C{<attribute>} - see the description of this element under
      L{ActionMapping<core.ActionMapping>}.
    - C{<renderer>} - see the description of this element under L{FormMetadata}.
  """
  def __init__(self, id, property, required, displayRequired, requiredErrorMessage, type, label,
      cssClass, hidden, maxlength = 0, validate = None, pythonClass = None,
      instruction = None, list = False, defaultValue = None):
    super(FieldMetadata,self).__init__(id, property, pythonClass, required,
      displayRequired, requiredErrorMessage, label, list, validate, instruction)
    self.type = type
    self.cssClass = cssClass
    self.hidden = hidden
    self._maxlength = maxlength
    self.defaultValue = defaultValue
  def getType(self, req=None, mapping=None):
    """Returns the L{TypeMetadata} for this field."""
    return self.type
  def getDisplay(self, req, mapping):
    if self.hidden:
      return DISPLAY_HIDDEN
    else:
      return DISPLAY_NORMAL
  def __getattr__(self, attr):
    if attr == "maxlength":
      typemax = self.type.maxlength
      fieldmax = self._maxlength
      if typemax and fieldmax:
        maxlength = min(typemax, fieldmax)
      else:
        maxlength = max(typemax, fieldmax)
      return maxlength
    else:
      raise AttributeError

class MetadataGroup(MetadataBase):
  """Metadata about a group of fields. This is done whenever a set of fields
  are logically associated to each other for both display and mapping to/from
  the model layer. A C{MetadataGroup} is defined in the application
  configuration xml file according to the following syntax:

  C{<fieldgroup>} tags takes the following attributes:
    - C{name} - the name of the field group. Must be unique within the form.
    - C{property} - Optional. The python property on the parent model object
      which represents the group of fields. If provided it means that this
      group of fields' values are on an object stored at this property.
    - C{python-class} - Optional. Similar to the python-class attribute of a
      form.
    - C{label} - The resource bundle key for displaying this group of fields.
    - C{list} - Optional. When set to C{true}, there is a list of these objects
      represented on the form. Lists of lists are not supported at this time,
      so once a field group has been declared as a list, the fields/groups
      within it should not be.
    - C{required} - Optional. The field group must be present on the form.
    - C{required-error-message} - Optional. Overrides the default message when
      the required field is missing. A resource bundle key.

  Additionally, a C{<fieldgroup>} can have the following child elements:
    - C{<field>} - see the description of this element under L{FieldMetadata}.
    - C{<fieldgroup>} - C{<fieldgroup>} elements can be nested arbitrarily deep.
    - C{<attribute>} - see the description of this element under
      L{ActionMapping<core.ActionMapping>}.
    - C{<validation>} - defines validation for the entire form. The field name
      will be L{GLOBAL<pywebmvc.framework.core.ActionError.GLOBAL>} when the
      group is the C{<form>}, otherwise the id of the C{<fieldgroup>}. See the
      documentation under L{TypeMetadata} for more details.

    - C{<renderer>} - defines the renderer class which is to be used for
      rendering a specific field or field type. C{<renderer>} takes the
      following attributes:
        - C{type} - one of the following values:
          - C{form}  - renders a form and is the renderer primarily handling the
            layout of the form on the page.
          - C{fieldgroup} - Renders a group of fields.
          - C{fieldgrouplist} - Renders a list of fieldgroups.
          - C{select} - Renders a drop down selection list.
          - C{multiselect} - Renders a multi-selection list.
          - C{radio} - Renders a single radio option
          - C{radiolist} - Renders a list of radio options (TODO: Rename this
            checkboxlist)
          - C{hidden} - Renders a hidden field
          - C{hiddenlist} - Renders a list of hidden fields
          - C{text} - Renders a text box
          - C{textlist} - Renders a list of text boxes
          - C{password} - Renders a password text box
          - C{passwordlist} - Renders a list of password text boxes
          - C{readonly} - Renders a read only field
          - C{readonlylist} - Renders a list of read only fields
          - C{label} - Renders a label
          - C{instruction} - Renders an instruction
          - C{required} - Renders the visual marker for a required field.
          - C{errors} - Renders a list of errors
          - C{error} - Renders a single error
          - C{checkbox} - Renders a checkbox
          - C{submit} - Renders a form submission button
          - C{submitlist} - Renders a list of form submission buttons.
    
        - C{python-class} - This is the python class which will be used
          instead of the factory default renderer for the specified type. Syntax
          is C{python.module::class}.
  """
  def __init__(self, id, property = None, pythonClass = None, required = False,
               displayRequired = None, requiredErrorMessage = None, label = None, list = False,
               validate = None, instruction = None):
    super(MetadataGroup,self).__init__( id, property, pythonClass, required, displayRequired,
      requiredErrorMessage, label, list, validate, instruction)
    self.subGroups = []
    self.metadataByName = {}
    self.metadataByProperty = {}
    self.order = []
    self.metadataClasses = {}
  def setMetadataClass(self, type, constructor):
    assert type in ("field", "fieldgroup", "form")
    self.metadataClasses[type] = constructor
  def addMetadata(self, metadata):
    """Add a metadata in this group. Can be another group or a field."""
    if self.hasProperty(metadata.property):
      raise PyWebMvcInvalidConfigurationException, ("property %s already exists in this context" % (metadata.property))
    form = self.getForm()
    if form.hasFieldMetadata(metadata.id):
      raise PyWebMvcInvalidConfigurationException, ('id "%s" already exists in form "%s"' % (metadata.id, form.id))
    if metadata.id == "_charset_":
      raise PyWebMvcInvalidConfigurationException, ('id "%s" is reserved for internal use.' % (metadata.id))
    metadata.setParent(self)
    self.order.append(metadata.id)
    if isinstance(metadata, MetadataGroup):
      self.subGroups.append(metadata)
    self.metadataByName[metadata.id] = metadata
    if metadata.property:
      self.metadataByProperty[metadata.property] = metadata
  def __getitem__(self, key):
    """dictionary access to get a child metadata by id"""
    return self.metadataByName[key]
  def keys(self):
    """get all the metadata id's of the child metadata."""
    return self.metadataByName.keys()
  def hasProperty(self, property):
    """check if there is metadata for the model-layer C{property}."""
    return property in self.metadataByProperty.keys()
  def getProperties(self):
    """get a list of all the model-layer properties of the child metadata."""
    return self.metadataByProperty.keys()
  def getMetadata(self, id):
    """get a child metadata from any depth"""
    if self.metadataByName.has_key(id):
      return self.metadataByName[id]
    else:
      for group in self.subGroups:
        if group.hasMetadata(id):
          return group.getMetadata(id)
    raise KeyError, id
  def hasMetadata(self, id):
    """check if there is a child metadata identified by C{id}."""
    if self.metadataByName.has_key(id):
      return True
    else:
      for group in self.subGroups:
        if group.hasMetadata(id):
          return True
    return False
  def hasFieldMetadata(self, id):
    """check if there is a descendent metadata for a field identified by
    C{id}."""
    if (self.metadataByName.has_key(id) and 
        isinstance(self.metadataByName[id], FieldMetadata)):
      return True
    else:
      for group in self.subGroups:
        if group.hasFieldMetadata(id):
          return True
    return False
  def getFieldNames(self):
    """get a list of all the descendent field names"""
    names = []
    for metadata in self.metadataByName.values():
      if isinstance(metadata, FieldMetadata):
        names.append(metadata.id)
    for group in self.subGroups:
      names += group.getFieldNames()
    return names
  def getFieldMetadata(self, id):
    """Retrieve the descendent L{FieldMetadata} identified by C{id} or raise
    L{KeyError} if not found.
    """
    if (self.metadataByName.has_key(id) and 
        isinstance(self.metadataByName[id], FieldMetadata)):
      return self.metadataByName[id]
    else:
      for group in self.subGroups:
        if group.hasFieldMetadata(id):
          return group.getFieldMetadata(id)
    raise KeyError, id
  def getMetadataByProperty(self, property):
    """get a child metadata defined for the specified model-layer
    C{property}."""
    return self.metadataByProperty[property]

class FormMetadata(MetadataGroup):
  """Additional metadata that is specific for the entire form. C{<form>} 
  elements accept all of the attributes and children as C{<fieldgroup>} with the exception of the C{property} attribute which does not apply here.


  C{<form>} has the following additional attributes beyond what is accepted for
  C{<fieldgroup>}:
    - C{focus} - Optional. the C{id} of a C{<field>} contained within the form. The
      input focus will be set to that field when the page first loads.
    - C{method} - The method by which the form will be sent to the web server.
      Can be C{post} or C{get}. Defaults to the browser default behavior for the
      form.

  For details on C{<fieldgroup>} see L{MetadataGroup}.
  """
  def __init__(self, id, pythonClass, tabIndexTable, validate= None,
               method=None, type=None, list=False, instruction=None):
    """constructor. C{tabIndexTable} is an instance of L{TabIndexTable<util>} so
    the form knows what tab index has been assigned to each field."""
    super(FormMetadata,self).__init__( id, None, pythonClass=pythonClass,
                           validate=validate, list=list, instruction=instruction)
    self.focus = None
    self.method = method
    self.type = type
    self.tabIndexTable = tabIndexTable
  def setFocus(self,fieldId):
    """Sets the field metadata id for the form."""
    self.focus = self.getFieldMetadata(fieldId)

class TypeMetadata(PyWebMvcObject):
  """Data about the type of a field.

  C{<type>} - The type element declares a field data type. Additionally it can
  take the following attributes:
    - C{id} - Identifier used for referencing to this type elsewhere in the
      configuration
    - C{input} - the html input type to be used. The following values are
      currently supported:
        - C{submit} - submits the form
        - C{checkbox} - a box that can be toggled on and off
        - C{text} - a single line of text input
        - C{password} - like text but the user's typing is replaced with *
        - C{select} - choices are presented from a list of possible values.  a
          validation of type enumeration is used to validate and create the
          list of legal inputs when used with the standard renderer. (TODO:
          need details on the data driven enumeration)
    - C{max-length} - Optional. The maximum string length of the entered value.

  Each type can have multiple C{<validation>} child elements which define the
  legal format for this type. More specific validation can be performed at the
  L{field level<FieldMetadata>}. When more than one validation is specified they
  must all be satisfied (boolean AND).

  C{<validation>} elements take the following attributes:
    - C{error-message} - a resource bundle key which defines the error message
      to be displayed when the validation fails.
    - C{type} - the validation type determines how the child C{<value>}
      elements are interpreted. the following types of validation are currently
      supported:
        - C{enumeration} - each C{<value>} is a interpreted as a possible legal
          value.  The value received from the user must match exactly to one of
          these C{<value>} elements.
        - C{regex} - only one C{<value>} child is allowed. The contents of
          which are interpreted as a regular expression.
        - C{function} - only one C{<value>} child is allowed and its contents
          are interpreted similarly to python-class. The imported object must
          be callable and accept three parameters: C{request}, C{form}, and
          C{fieldName}.  The value can to be retrieved by C{form[fieldName]},
          by passing the value in this way, validator functions can perform
          validation dependent on another field's values. The callable should
          return an L{ActionErrors<core>} object.
  C{<value>} elements enclose their value with a start and end tag.
  Additionally, they take the following attributes:
    - C{label} - A resource bundle key which can be used to display the value.
      Only used in conjunction with an C{enumeration} C{<validation>}.
  """
  def __init__(self, id, input, maxlength, validateFunc):
    self.id = id
    self.input = input
    self.maxlength = maxlength
    self.validate = validateFunc

