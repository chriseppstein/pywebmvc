#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

"""Render text to the form."""

from types import *
from pywebmvc.framework import htmlutil, metadata
from pywebmvc.framework.core import ActionError, PyWebMvcException
from pywebmvc.framework.metadata import FieldMetadata, MetadataGroup

from __init__ import Renderer

class InstructionRenderer(Renderer):
  def getInstruction(self, request, mapping, name, instruction,**kwargs):
    if instruction is None:
      instructionKey = mapping.getFormMetadata(request).getMetadata(name).getInstruction(request,mapping)
      if not instructionKey:
        instructionKey = "instruction.%s.%s" % (mapping.getFormMetadata(request).id, name)
      if request.bundle.has_key(instructionKey):
        instruction = request.bundle[instructionKey]
      else:
        instruction = ""
    return instruction
  def render(self,request, mapping, name, instruction = None,**kwargs):
    instruction = self.getInstruction(request,mapping,name,instruction,**kwargs)
    if instruction:
      html = '<div class="pyWebMvcInstruction">'
      html += instruction
      html += '</div>'
      return html
    else:
      return ""

class ReadOnlyRenderer(Renderer):
  def renderValue(self, value, cssClass):
    if not value:
      value = "&nbsp;"
    if cssClass:
      return '<span class="%s">%s</span>' %(cssClass, unicode(value))
    else:
      return unicode(value)
  def render(self, request, mapping, name, value, cssClass, **kwargs):
    displayValue = value
    if kwargs.has_key("options") and kwargs["options"]:
      for opt in kwargs["options"]:
        if unicode(opt["value"]) == unicode(value):
          displayValue = request.bundle[opt["label"]]
          break
    html = self.renderValue(displayValue, cssClass)
    hiddenRenderer = self.getRenderer(request,mapping,self.TYPE_HIDDEN,name)
    html += hiddenRenderer.render(request, mapping, name, value)
    return html

class LabelRenderer(Renderer):
  def render(self,request, mapping, label, cssClass, *args, **kwargs):
    return '<label class="%s"%s>%s</label>' % (cssClass, self.renderAttributes(kwargs), label)

class RequiredRenderer(Renderer):
  def render(self,request, mapping, *args, **kwargs):
    return '<span class="required">*</span>'

class ErrorsRenderer(Renderer):
  def render(self,request, mapping, name, errors, *args, **kwargs):
    errorRenderer = self.getRenderer(request,mapping, Renderer.TYPE_ERROR, name)
    if len(errors) > 1:
      errStr = '<ul class="pyWebMvcErrors">'
      for err in errors:
        errStr += '<li>'+errorRenderer.render(request,mapping,name,err)+'</li>'
      errStr += '</ul>'
      return errStr
    else:
      for err in errors:
        return '<span class="pyWebMvcError">'+errorRenderer.render(request,mapping,name,err)+'</span>'

class ErrorRenderer(Renderer):
  def render(self, request, mapping, name, error, *args, **kwargs):
    return error.message

class ReadOnlyListRenderer(Renderer):
  def __init__(self, elementStart = "", elementEnd = "", separator = "<br>"):
    self.separator = separator
    self.elementStart = elementStart
    self.elementEnd = elementEnd
  def render(self, request, mapping, name, values, cssClass,
               *args,**kwargs):
    first = True
    html = ""
    readOnlyRenderer = self.getRenderer(request,mapping,self.TYPE_READ_ONLY, name)
    for v in values:
      if not first:
        html += self.separator
      else:
        first = False
      html += self.elementStart
      html += readOnlyRenderer.render(request, mapping, name, v, cssClass)
      html += self.elementEnd
    return html

class ReadOnlyCommaListRenderer(ReadOnlyListRenderer):
  def __init__(self, readOnlyRenderer = None):
    ReadOnlyListRenderer.__init__(Self, readOnlyRenderer, "", "", ", ")

class ReadOnlyOrderedListRenderer(ReadOnlyListRenderer):
  def __init__(self, readOnlyRenderer = None):
    ReadOnlyListRenderer.__init__(Self, readOnlyRenderer, "<li>", "</li>","")
  def render(self, request, mapping, values, name, cssClass,
               *args,**kwargs):
    return "<ol>"+super(ReadOnlyOrderedListRenderer,self).render( request, mapping,
           values, name, cssClass, *args,**kwargs)+"</ol>"

class ReadOnlyUnorderedListRenderer(ReadOnlyListRenderer):
  def __init__(self, readOnlyRenderer = None):
    ReadOnlyListRenderer.__init__(Self, readOnlyRenderer, "<li>", "</li>","")
  def render(self, request, mapping, values, name, cssClass,
               *args,**kwargs):
    return "<ul>"+super(ReadOnlyUnorderedListRenderer,self).render( request, mapping,
           values, name, cssClass, *args,**kwargs)+"</ul>"


