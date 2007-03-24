#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

"""Render widgets which take input from the user."""

from types import *
from pywebmvc.framework import htmlutil, metadata
from pywebmvc.framework.core import ActionError, PyWebMvcException
from pywebmvc.framework.metadata import FieldMetadata, MetadataGroup

from __init__ import Renderer, MutableListRenderer, ListRenderer

class WidgetRenderer(Renderer):
  """Base class for all input widgets"""
  def render(self, request, mapping, name, value, cssClass, **kwargs):
    """**kwargs is a mapping of additional html attibute/values
       to be rendered."""
    display = metadata.DISPLAY_NORMAL
    if kwargs.has_key("display"):
      display = kwargs["display"]    
    if display == metadata.DISPLAY_HIDDEN:
      return self.renderHidden(request, mapping, name, value, cssClass, **kwargs)
    elif display == metadata.DISPLAY_READONLY:
      return self.renderReadOnly(request, mapping, name, value, cssClass, **kwargs)
    else:
      return self.renderNormal(request, mapping, name, value, cssClass, **kwargs)
  def renderNormal(self, request, mapping, name, value, cssClass, **kwargs):
    """All Subclasses must implement this method for normal read-write rendering."""
    return ""
  def renderReadOnly(self, request, mapping, name, value, cssClass, **kwargs):
    """Subclasses may implement this method for custom read-only rendering.  Otherwise, rendering is redirected to the generic read-only renderer."""
    fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
    if fmd.list:
      type = Renderer.TYPE_READ_ONLY_LIST
    else:
      type = Renderer.TYPE_READ_ONLY
    redirect = self.getRenderer(request, mapping, type, name)
    return redirect.render(request, mapping, name, value, cssClass, **kwargs)
  def renderHidden(self, request, mapping, name, value, cssClass, **kwargs):
    """Subclasses may implement this method for custom hidden field rendering.  Otherwise, rendering is redirected to the generic hidden renderer."""
    fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
    if fmd.list:
      type = Renderer.TYPE_HIDDEN_LIST
    else:
      type = Renderer.TYPE_HIDDEN
    redirect = self.getRenderer(request, mapping, type, name)
    return redirect.render(request, mapping, name, value, cssClass, **kwargs)

def appendJavascriptToValue(kwargs, attributeName, valueToAppend):
  if(kwargs.has_key(attributeName)):
    kwargs[attributeName] += ';' + valueToAppend
  else:
    kwargs[attributeName] = valueToAppend

class InputRenderer(WidgetRenderer):
  def __init__(self, type="text"):
    self.type = type
  def renderNormal(self, request, mapping, name, value, cssClass, **kwargs):
    if kwargs.has_key("id"):
      id = kwargs["id"]
    else:
      id = name
    inputHtml = '<input type="%s" id="%s" name="%s" value="%s"' % (self.type, id, name, htmlutil.escapeAttribute(unicode(value)))
    if cssClass:
      inputHtml += ' class="%s"' % (cssClass)
    argsCopy = kwargs.copy()
    appendJavascriptToValue(argsCopy, 'onkeypress',  'returnKeyPressedInIEHandler(event)')
    inputHtml += self.renderAttributes(argsCopy)
    inputHtml += '>'
    return inputHtml

class TextAreaRenderer(WidgetRenderer):
  def renderNormal(self, request, mapping, name, value, cssClass, **kwargs):
    html = '<textarea id="%s" name="%s"' % (name, name,)
    if cssClass:
      html += ' class="%s"' % (cssClass)
    html += self.renderAttributes(kwargs)
    html += '>%s</textarea>' % (htmlutil.escapeHtml(value),)
    return html

class TextInputRenderer(InputRenderer):
  def __init__(self):
    super(TextInputRenderer,self).__init__("text")

class TextListRenderer(MutableListRenderer):
  def __init__(self):
    super(TextListRenderer,self).__init__( self.TYPE_TEXT)

class PasswordInputRenderer(InputRenderer):
  def __init__(self):
    super(PasswordInputRenderer,self).__init__("password")
  def renderNormal(self, request, mapping, name, value, cssClass, **kwargs):
    return super(PasswordInputRenderer,self).renderNormal( request, mapping, name, value, cssClass, maxlength=20, **kwargs)


class PasswordListRenderer(MutableListRenderer):
  def __init__(self):
    super(PasswordListRenderer,self).__init__( self.TYPE_PASSWORD)

class OptionsListRenderer(ListRenderer):
  def render(self, request, mapping, name, values, cssClass, **kwargs):
    options = kwargs["options"]
    del kwargs["options"]
    elementRenderer = self.getRenderer(request,mapping, self.type, name)
    html = ""
    first = True
    for o in options:
      if first:
        first = False
      else:
        html += self.separator
      html += self.before + elementRenderer.render(request, mapping, name,
              o["value"], cssClass, request.bundle[o["label"]], **kwargs) + self.after
    return html


class SubmitRenderer(WidgetRenderer):
  def renderNormal(self, request, mapping, name, value, cssClass, label = None, **kwargs):
    if kwargs.has_key("display") and kwargs["display"] != metadata.DISPLAY_NORMAL:
      return ""
    if name == "submit":
      raise ValueError("\"submit\" is not a valid field name")
    if not label:
      label = request.bundle[mapping.getFormMetadata(request).getFieldMetadata(name).getLabel(request,mapping)]
    html = '<button'
    if cssClass:
      kwargs["class"] = cssClass
    if kwargs.has_key("onclick"):
      onclick = kwargs["onclick"]+";"
    else:
      onclick = ""
    onclick += "resetSubmitButtons(); this.nextSibling.disabled = false; var p = this.parentNode; while (p.tagName.toLowerCase() != 'form') p = p.parentNode; try { p.submit(); } catch (e) {this.nextSibling.disabled = true;}"
    kwargs["onclick"] = onclick
    html += self.renderAttributes(kwargs)
    html += ' pwmvctype="submit">%s</button>' % htmlutil.escapeHtml(label)
    html += '<input type="hidden" name="%s" value="%s" disabled="disabled">' % (name, htmlutil.escapeAttribute(value))
    return html
  def renderReadOnly(self, request, mapping, name, value, cssClass, label = None, **kwargs):
    return self.renderNormal(request, mapping, name, value, cssClass, label, **kwargs)

class SubmitListRenderer(OptionsListRenderer):
  def __init__(self, before = "", after = "", separator = ""):
    super(SubmitListRenderer,self).__init__(self.TYPE_SUBMIT,before,after,separator)

class SelectRenderer(WidgetRenderer):
  def __init__(self, multiSelect=False):
    self.multiSelect = multiSelect
  def renderSelect(self,request, mapping, name, value, cssClass, readOnly, **kwargs):
    options = kwargs["options"]
    del kwargs["options"]
    html = '<select id="%s" name="%s"' % (name, name)
    if readOnly:
      html += ' disabled'
    if cssClass:
      html += ' class="%s"' % (cssClass)
    if self.multiSelect:
      html += ' multiple="multiple"'
    html += self.renderAttributes(kwargs)
    html += '>' 
    for option in options:
      html += '<option value="%s"' % (option["value"])
      if value and (
         (isinstance(value,ListType) and option["value"] in value) or
         (option["value"] == value)):
        html += ' selected="selected"'
      html += '>%s</option>' % (request.bundle[option["label"]])
    html += "</select>"
    return html
  def renderNormal(self,request, mapping, name, value, cssClass, **kwargs):
    return self.renderSelect(request, mapping, name, value, cssClass, False, **kwargs)
  def renderReadOnly(self,request, mapping, name, value, cssClass, **kwargs):
    return self.renderSelect(request, mapping, name, value, cssClass, True, **kwargs)
  
  

class RadioRenderer(WidgetRenderer):
  def __init__(self, multiSelect=False, insertBreak=False):
    self.multiSelect = multiSelect
    self.insertBreak = insertBreak
  def renderNormal(self,request, mapping, name, value, cssClass, **kwargs):
    if self.multiSelect:
      type = 'checkbox'
    else:
      type = 'radio'
    html = ""
    options = kwargs["options"]
    del kwargs["options"]
    for option in options:
      html += '<input type="%s" id="%s" name="%s" value="%s"' % (type,
        name, name, htmlutil.escapeAttribute(option["value"]))
      if value is not None and (
         (isinstance(value,ListType) and option["value"] in value) or
         (option["value"] == unicode(value))):
        html += ' checked="checked"'
      html += self.renderAttributes(kwargs)
      html += '>&nbsp;<span onclick="this.previousSibling.previousSibling.click();" style="cursor: pointer;">%s</span>' % (request.bundle[option["label"]])
      if self.insertBreak:
        html += "<br>"
    return html

class MultilineRadioRenderer(RadioRenderer):
  def __init__(self):
    super(MultilineRadioRenderer,self).__init__(False,True)

class RadioListRenderer(RadioRenderer):
  def __init__(self):
    super(RadioListRenderer,self).__init__(False)

class MultiSelectRenderer(SelectRenderer):
  def __init__(self):
    super(MultiSelectRenderer,self).__init__(True)

class CheckboxRenderer(WidgetRenderer):
  def renderCheckbox(self,request, mapping, name, value, cssClass, readOnly, **kwargs):
    id = name
    if kwargs.has_key("index"):
      id += "__"+str(kwargs["index"])
    hiddenId = id + "__hidden"
    html = '<input type="checkbox" id="%s"' % (id)
    if value:
      html += ' checked="checked"'
      value = "on"
    else:
      value = "off"
    if readOnly:
      html += ' disabled'
    if cssClass:
      html += ' class="%s"' % (cssClass)
    if kwargs.has_key("onclick"):
      onclick = kwargs["onclick"]
      del kwargs["onclick"]
    else:
      onclick = ""
    html += ' onclick="this.nextSibling.value=(this.checked?\'on\':\'off\');%s"' % (onclick)
    html += self.renderAttributes(kwargs)
    html += '>'
    html += '<input type="hidden" id="%s" name="%s" value="%s">' % (hiddenId, name,value)
    html += """<script type="text/javascript">
                document.getElementById("%(hiddenId)s").value = document.getElementById("%(id)s").checked?"on":"off";
               </script>
            """ % {"id" : id, "hiddenId" : hiddenId}
    return html
  def renderNormal(self,request, mapping, name, value, cssClass, **kwargs):
    return self.renderCheckbox(request, mapping, name, value, cssClass, False, **kwargs)
  def renderReadOnly(self,request, mapping, name, value, cssClass, **kwargs):
    return self.renderCheckbox(request, mapping, name, value, cssClass, True, **kwargs)

class FileRenderer(InputRenderer):
  def __init__(self):
    super(FileRenderer, self).__init__("file")

class HiddenRenderer(Renderer):
  def render(self,request, mapping, name, value, *args, **kwargs):
    return ( '<input type="hidden" name="%s" value="%s" %s>' %
            (name, htmlutil.escapeAttribute(unicode(value)), self.renderAttributes(kwargs)) )

class HiddenListRenderer(Renderer):
  def render(self,request, mapping, name, values):
    html = ""
    hiddenRenderer = self.getRenderer(request,mapping,self.TYPE_HIDDEN,name)
    for v in values:
      html += hiddenRenderer.render(request, mapping, name, v)
    return html
