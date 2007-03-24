#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""Validation functions and utilities.
"""
import re, types
from core import ActionError, ActionErrors
from util import PyWebMvcObject

def createMultiValidator(*args):
  """returns a function which calls to all of the validation functions
  passed as C{args} and aggregates the errors returned."""
  def validator(request, mapping, form, fieldName):
    errors = ActionErrors()
    for f in args:
      errors.addAll(f(request, mapping, form, fieldName))
    return errors
  return validator 


class EnumValidatorBase(PyWebMvcObject):
  """Base class for the Enumeration Validators: L{EnumValidator} and
  L{EnumGeneratorValidator}."""
  def __init__(self, errorMsgKey):
    self.errorMsgKey = errorMsgKey
  def getValueLabelList(self, req):
    assert("Override")
  def getValues(self, req):
    return map(lambda val: val["value"], self.getValueLabelList(req))
  def __call__(self, request, mapping, form, fieldName):
    errors = ActionErrors()
    if form.has_key(fieldName) and len(form[fieldName]) > 0:
      validValues = self.getValues(request)
      value = form[fieldName]
      if isinstance(value, types.ListType):
        index = 0
        for v in value:
          if not (v in validValues):
            errors.add(ActionError(fieldName,
              request.bundle[self.errorMsgKey],index))
          index += 1
      else:
        if not (value in validValues):
          errors.add(ActionError(fieldName, request.bundle[self.errorMsgKey]))
    return errors
  

class EnumValidator(EnumValidatorBase):
  """Validates that the value passed in is one of the values
  passed to the constructor."""
  def __init__(self, values, errorMsgKey):
    super(EnumValidator,self).__init__( errorMsgKey)
    self.__values = values
  def getValueLabelList(self, req):
    return self.__values


class EnumGeneratorValidator(EnumValidatorBase):
  """Validates that the value passed in is one of the values
  returned by the C{generationFunction}."""
  def __init__(self, generationFunction, errorMsgKey):
    super(EnumGeneratorValidator,self).__init__(errorMsgKey)
    self.generator = generationFunction
  def getValueLabelList(self, req):
    return self.generator(req)


def createEnumValidator(values, errorMsgKey):
  """Creates an L{EnumValidator}."""
  return EnumValidator(values, errorMsgKey)

def createEnumGeneratorValidator(generationFunction, errorMsgKey):
  """Creates an L{EnumGeneratorValidator}."""
  return EnumGeneratorValidator(generationFunction, errorMsgKey)

def createRegexValidator(regexStr, errorMsgKey):
  """Creates a validation function that validate the value matches the supplied
  regular expression C{regexStr}."""
  regex = re.compile(regexStr)
  def validator(request, mapping, form, fieldName, value = None):
    fieldMetadata = mapping.getFormMetadata(request).getFieldMetadata(fieldName)
    errors = ActionErrors()
    if value is None and form.has_key(fieldName):
      value = form[fieldName]
    if isinstance(value, types.ListType):
      index = 0
      for v in value:
        fieldErrors = validator(request, mapping, form, fieldName, v)
        for error in fieldErrors:
          error.index = index
        errors.addAll(fieldErrors)
        index += 1
    else:
      if not (value is None) and len(value) > 0:
        if not regex.search(value):
          if not fieldMetadata.getLabel(request,mapping):
            fieldLabel = fieldName
          else:
            fieldLabel = request.bundle[fieldMetadata.getLabel(request,mapping)]
          errors.add(ActionError(fieldName, request.bundle.getMessage(errorMsgKey,fieldLabel)))
    return errors
  return validator


ipaddressRegex = re.compile("^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
def validateIPAddress(request, mapping, form, fieldName, value = None):
  """validates the value is an IP Address."""
  errors = ActionErrors()
  if value is None:
    value = form[fieldName]
  if isinstance(value, types.ListType):
    index = 0
    for item in value:
      if not (item is None):
        fieldErrors = validateIPAddress(request, mapping, form, fieldName, item)
        for e in fieldErrors:
          e.index = index
        errors.addAll(fieldErrors)
      index += 1
  else:
    match = ipaddressRegex.search(value)
    if match:
      for group in match.groups():
        if int(group) > 255:
          errors.add(ActionError(fieldName,
            request.bundle["error.ipAddress.range"]))
          break
  return errors

timeRegex = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2})(:(?P<s>\d{2}))?$")
def validateTime(request, mapping, form, fieldName, value = None):
  """validates the value is a time in the format hh:mm:ss."""
  errors = ActionErrors()
  if value is None:
    value = form[fieldName]
  if isinstance(value, types.ListType):
    index = 0
    for item in value:
      if not (item is None):
        fieldErrors = validateTime(request, mapping, form, fieldName, item)
        for e in fieldErrors:
          e.index = index
        errors.addAll(fieldErrors)
      index += 1
  else:
    match = timeRegex.search(value)
    if match:
      if int(match.group("h")) > 23:
        errors.add(ActionError(fieldName,
          request.bundle.getMessage("error.time.hour.range", request.bundle[mapping.getFormMetadata(request).getFieldMetadata(fieldName).getLabel(request,mapping)])))
      if int(match.group("m")) > 59:
        errors.add(ActionError(fieldName,
          request.bundle.getMessage("error.time.minute.range", request.bundle[mapping.getFormMetadata(request).getFieldMetadata(fieldName).getLabel(request,mapping)])))
      if match.group("s"):
        if int(match.group("s")) > 59:
          errors.add(ActionError(fieldName,
            request.bundle.getMessage("error.time.second.range", request.bundle[mapping.getFormMetadata(request).getFieldMetadata(fieldName).getLabel(request,mapping)])))
  return errors

def integer(request, form, fieldName):
  """validates the value is an integer."""
  errors = ActionErrors()
  try:
    int(form[fieldName])
  except:
    errors.add(ActionError(fieldName,
      request.bundle["error.integer"]))
  return errors

def nonNegativeInteger(request, form, fieldName):
  """validates the value is a non-negative integer."""
  errors = ActionErrors()
  try:
    value = int(form[fieldName])
    if value < 0:
      errors.add(ActionError(fieldName,
        request.bundle["error.nonNegativeInteger"]))
  except:
    errors.add(ActionError(fieldName,
      request.bundle["error.nonNegativeInteger"]))
  return errors

def requiredError(req, mapping, fieldName, fieldMetadata):
  """gets the L{ActionError} for the field when the required value is not
  provided."""
  parameters = []
  if fieldMetadata.getRequiredErrorMessage(req):
    key = fieldMetadata.getRequiredErrorMessage(req)
    requiredLabel = False
  else:
    key = "pywebmvc.message.requiredField"
    requiredLabel = True
  if fieldMetadata.getLabel(req,mapping):
    parameters.append(req.bundle[fieldMetadata.getLabel(req,mapping)])
  elif requiredLabel:
    raise PyWebMvcInvalidConfigurationException(("Required field '%s' on "+\
    "form '%s' must have a label or provide it's own required error message.")
    % ( fieldMetadata.id, fieldMetadata.getForm().id))
  errorMsg = req.bundle.getMessage(key, *parameters)
  return ActionError(fieldName, errorMsg)


def validateRequired(req, mapping, value, fieldName,  fieldMetadata):
  """validates the field to ensure required values are provided."""
  errors = ActionErrors()
  if fieldMetadata.isRequired(req, mapping):
    if isinstance(value, types.ListType):
      if not value:
        e = requiredError(req,mapping,fieldName,fieldMetadata)
        e.index = 0
        errors.add(e)
      else:
        index = 0
        for v in value:
          if fieldMetadata.getType(req, mapping).input == "file":
            try:
              if not v.file.read(1):
                e = requiredError(req, mapping, fieldName,fieldMetadata)
                e.index = index
                errors.add(e)
            finally:
              v.file.seek(0)
          elif not v:
            e = requiredError(req, mapping, fieldName,fieldMetadata)
            e.index = index
            errors.add(e)
          index += 1
    elif fieldMetadata.getType(req, mapping).input == "checkbox":
      if not req.form.has_key(fieldName+"__onpage"):
        e = requiredError(req, mapping, fieldName,fieldMetadata)
        e.index = 0
        errors.add(e)
    if fieldMetadata.getType(req, mapping).input == "file":
      try:
        if not value.file.read(1):
          e = requiredError(req, mapping, fieldName,fieldMetadata)
          errors.add(e)
      finally:
        value.file.seek(0)
    elif not value:
      e = requiredError(req, mapping, fieldName,fieldMetadata)
      e.index = 0
      errors.add(e)
  return errors

def validateForm(req, mapping):
  """Validates the entire form and returns an L{ActionErrors} object with the
  results. If no error is found, the C{ActionErrors} object is empty.  Fields
  are validated before the form-level validation is performed. Form-level
  validation is only performed when all fields are valid."""
  errors = ActionErrors()
  hasFieldErrors = False
  for fieldName in mapping.getFormMetadata(req).getFieldNames():
    value = None
    if req.form.has_key(fieldName):
      value = req.form[fieldName]
    fieldMetadata = mapping.getFormMetadata(req).getFieldMetadata(fieldName)
    reqErrors = validateRequired(req, mapping, value, fieldName,  fieldMetadata)
    if reqErrors:
      hasFieldErrors = True
    if reqErrors and fieldMetadata.defaultValue:
      if fieldMetadata.list:
        req.form[fieldName] = [fieldMetadata.defaultValue]
      else:
        req.form[fieldName] = fieldMetadata.defaultValue
    else:
      errors.addAll(reqErrors)
    if not reqErrors:
      fieldErrors = fieldMetadata.getType(req, mapping).validate(req, mapping, req.form, fieldName)
      if not fieldErrors:
        fieldErrors = fieldMetadata.validate(req, mapping, req.form, fieldName)
      if fieldErrors:
        hasFieldErrors = True
      errors.addAll(fieldErrors)
  if not hasFieldErrors:
    errors.addAll(mapping.getFormMetadata(req).validate(req, mapping, req.form, ActionError.GLOBAL))
  return errors
