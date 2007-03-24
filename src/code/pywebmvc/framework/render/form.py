#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

"""Render collections of fields (forms and fieldgroups)."""

from types import *
from pywebmvc.framework import htmlutil, metadata
from pywebmvc.framework.core import ActionError, PyWebMvcException
from pywebmvc.framework.metadata import FieldMetadata, MetadataGroup
from __init__ import Renderer

class MetadataRenderer(Renderer):
  """Abstract Base class providing utilites which render based on
     configuration metadata.
  """
  def checkMetadata(self, request, mapping, metadata):
    if isinstance(metadata, StringTypes):
      return mapping.getFormMetadata(request).getMetadata(metadata)
    else:
      return metadata
  def getAttributes(self, request, mapping, name, attributes):
    """sets any attributes from the config file which are not explicitly
       set already"""
    if mapping.getFormMetadata(request).hasFieldMetadata(name):
      fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
      for key in fmd.attributes.keys():
        if not attributes.has_key(key):
          #str:notok -- but kwargs usage requires this
          attributes[str(key)] = unicode(fmd.attributes[key])
  def hasError(self,request, mapping, name, index = None):
    if hasattr(request,"errors"):
      return request.errors.hasError(name, index)
    else:
      return False
  def errors(self,request, mapping, name, index = None):
    if self.hasError(request, mapping,name, index):
      errs = request.errors.getErrors(name, index)
      if errs:
        errorsRenderer = self.getRenderer(request,mapping, self.TYPE_ERRORS, name)
        return errorsRenderer.render(request, mapping, name, errs)
    return ""
  def getOptions(self, request, mapping, name, attributes):
    """Turns an enumerated validator into a set of legal options for a drop
       down list"""
    if not attributes.has_key("options"):
      options = []
      if mapping.getFormMetadata(request).hasFieldMetadata(name):
        fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
        tmd = fmd.getType(request, mapping)
        if hasattr(fmd.validate, "getValueLabelList"):
          options += fmd.validate.getValueLabelList(request)
        if hasattr(tmd.validate, "getValueLabelList"):
          options += tmd.validate.getValueLabelList(request)
        attributes["options"] = options
  def getDisplayValue(request, mapping, name, value, options = None):
    """for enumerated types: converts the value to a corresponding label"""
    options = self.getOptions(request, mapping, name, options)
    if isinstance(value, ListType):
      displayValue = []
      for v in value:
        for option in options:
          if (option["value"] == value):
            displayValue.append(request.bundle[option["label"]])
    else:
      displayValue = value
      for option in options:
        if (option["value"] == value):
          displayValue = request.bundle[option["label"]]
    return displayValue
  def getWidgetRenderer(self, request, mapping, name, display = None):
    """Returns the correct widget renderer for the field"""
    fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
    display = self.getDisplay(request,mapping,name,display)
    type = None
    if fmd.getType(request, mapping).input == Renderer.TYPE_SELECT:
      if fmd.list:
        type = Renderer.TYPE_SELECT_LIST
      else:
        type = Renderer.TYPE_SELECT
    elif fmd.getType(request, mapping).input == Renderer.TYPE_RADIO:
      if fmd.list:
        type = Renderer.TYPE_RADIO_LIST
      else:
        type = Renderer.TYPE_RADIO
    elif fmd.getType(request, mapping).input == Renderer.TYPE_TEXT:
      if fmd.list:
        type = Renderer.TYPE_TEXT_LIST
      else:
        type = Renderer.TYPE_TEXT
    elif fmd.getType(request, mapping).input == Renderer.TYPE_TEXT_AREA:
      if fmd.list:
        raise ValueError("Lists of text areas are not implemented")
      else:
        type = Renderer.TYPE_TEXT_AREA
    elif fmd.getType(request, mapping).input == Renderer.TYPE_PASSWORD:
      if fmd.list:
        type = Renderer.TYPE_PASSWORD_LIST
      else:
        type = Renderer.TYPE_PASSWORD
    elif fmd.getType(request, mapping).input == Renderer.TYPE_CHECKBOX:
      if fmd.list:
        raise ValueError("Lists of type checkbox are not allowed - use radio")
      else:
        type = Renderer.TYPE_CHECKBOX
    elif fmd.getType(request, mapping).input == Renderer.TYPE_SUBMIT:
      if fmd.list:
        type = Renderer.TYPE_SUBMIT_LIST
      else:
        type = Renderer.TYPE_SUBMIT
    elif fmd.getType(request, mapping).input == Renderer.TYPE_FILE:
      if fmd.list:
        type = Renderer.TYPE_FILE_LIST
      else:
        type = Renderer.TYPE_FILE
    else:
      type = fmd.getType(request, mapping).input
    return self.getRenderer(request,mapping, type, name)
  def instruction(self, request, mapping, name, widgetDisplay = None):
    instructionRenderer = self.getRenderer(request,mapping,self.TYPE_INSTRUCTION,name)
    instructionHtml = instructionRenderer.render(request, mapping, name)
    return instructionHtml
  def widget(self, request, mapping, name,
             defaultValue = None, display = None, cssClass = None, 
             **kwargs):
    """returns a rendered input widget for the given name.
       Setting any of the optional parameters will override metadata
       configuration file settings.
       kwargs is a mapping which will render arbitrary html attributes
       along with the tag -- useful for javascript event handlers etc."""
    display = self.getDisplay(request, mapping, name, display)
    kwargs["display"] = display
    #str:ok
    kwargs["tabindex"] = str(mapping.getFormMetadata(request).tabIndexTable.lookup(name))
    cssClass = self.getCssClass(request, mapping, name, cssClass)
    if kwargs.has_key("index"):
      index = kwargs["index"]
    else:
      index = None
    value = self.getValue(request, mapping, name, defaultValue, index)
    self.getMaxLength(request, mapping, name, kwargs)
    self.getOptions(request, mapping, name, kwargs)
    self.getAttributes(request, mapping, name, kwargs)
    renderer = self.getWidgetRenderer(request, mapping, name, display)
    return renderer.render(request, mapping, name, value, cssClass, **kwargs)
  def getLabelKey(self, request, mapping, name, labelKey):
    if not labelKey:
      fieldMetadata = mapping.getFormMetadata(request).getFieldMetadata(name)
      if fieldMetadata.getLabel(request, mapping):
        labelKey = fieldMetadata.getLabel(request, mapping)
    return labelKey
  def getRequired(self, request, mapping, name, required):
    if required is None:
      if mapping.getFormMetadata(request):
        fieldMetadata = mapping.getFormMetadata(request).getFieldMetadata(name)
        required = fieldMetadata.displayRequired(request, mapping)
      else:
        required = False
    return required
  def label(self, request, mapping, name, required = None, labelKey = None,
            cssClass = None, widgetDisplay=None, **kwargs):
    fieldMetadata = mapping.getFormMetadata(request).getFieldMetadata(name)
    typeMetadata = fieldMetadata.getType(request, mapping)
    widgetDisplay = self.getDisplay(request,mapping,name,widgetDisplay)
    required = self.getRequired(request,mapping,name,required)
    labelKey = self.getLabelKey(request,mapping,name,labelKey)
    if labelKey is None or \
        typeMetadata.input in  ("submit"):
      "Don't display a label in readonly, the input will output a label instead"
      return ""
    if not cssClass:
      cssClass = ""
    label = request.bundle[labelKey]
    labelRenderer = self.getRenderer(request,mapping, self.TYPE_LABEL,name)
    kwargs["for"] = name
    labelHtml = labelRenderer.render(request, mapping, label, cssClass, **kwargs)
    del kwargs["for"]
    if required:
      if not (typeMetadata.input in ("checkbox", "select", "submit", "radio") or
              widgetDisplay in (metadata.DISPLAY_READONLY,
                                metadata.DISPLAY_HIDDEN)):
        reqRenderer = self.getRenderer(request,mapping, self.TYPE_REQUIRED,name)
        labelHtml += reqRenderer.render(request, mapping)
    return labelHtml 
  def getValue(self, request, mapping, name, defaultValue = None, index = None):
    value = ""
    if mapping.getFormMetadata(request) and mapping.getFormMetadata(request).hasFieldMetadata(name):
      fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
    else:
      fmd = None
    if request.form.has_key(name):
      value = request.form[name]
      if isinstance(value, ListType) and not (index is None):
        if fmd and fmd.list:
          raise PyWebMvcException("index not allowed with list fields")
        value = value[index]
    elif fmd and fmd.getType(request, mapping).input == "checkbox" and request.form.has_key(name+"__onpage"):
      value = "off"
    elif defaultValue:
      value = unicode(defaultValue)
    elif fmd and fmd.defaultValue:
      value = fmd.defaultValue
    if fmd:
      try:
        if fmd.pythonClass:
          value = fmd.pythonClass(value)
      except:
        pass
      if fmd.list:
        if value is None:
          value = []
        elif not isinstance(value, ListType):
          value = [value]
    return value
  def getCssClass(self, request, mapping, name, cssClass):
    if not cssClass:
      if mapping.getFormMetadata(request):
        cssClass = mapping.getFormMetadata(request).getFieldMetadata(name).cssClass
      else:
        cssClass = ""
    return cssClass
  def getMaxLength(self, request, mapping, name, attributes):
    if not attributes.has_key("maxlength"):
      if mapping.getFormMetadata(request):
        fmd = mapping.getFormMetadata(request).getFieldMetadata(name)
      else:
        fmd = None
      if fmd and fmd.maxlength:
        attributes["maxlength"] = fmd.maxlength
  def getDisplay(self, request, mapping, name, display = None):
    if display == None:
      if mapping.getFormMetadata(request):
        display = mapping.getFormMetadata(request).getFieldMetadata(name).getDisplay(request, mapping)
      else:
        display = metadata.DISPLAY_NORMAL
    return display

class FieldGroupListRenderer(MetadataRenderer):
  def render(self, request, mapping, name, **kwargs):
    raise PyWebMvcException("Not Yet Implemented")

class FieldGroupRenderer(MetadataRenderer):
  def renderErrors(self, request, mapping, name):
    if self.hasError(request, mapping, name):
      return """<div class="pyWebMvcError">
             """+self.errors(request,mapping,name)+"""
             </div>"""
    return ""
  def renderFields(self, request, mapping, metadataGroup = None,**kwargs):
    fields = ""
    if metadataGroup is None:
      metadataGroup = mapping.getFormMetadata(request)
    if metadataGroup is None:
      return ""
    for id in metadataGroup.order:
      metadata = metadataGroup[id]
      if isinstance(metadata, FieldMetadata):
        fields += self.renderField(request, mapping, metadata,**kwargs)
      elif isinstance(metadata, MetadataGroup):
        fields += self.renderFieldGroup(request, mapping, metadata,**kwargs)
    return fields
  def renderFieldGroup(self, request, mapping, metadata,**kwargs):
    metadata = self.checkMetadata(request, mapping, metadata)
    if metadata.list:
      groupRenderer = self.getRenderer(request,mapping, self.TYPE_FIELD_GROUP_LIST, metadata.id)
    else:
      groupRenderer = self.getRenderer(request,mapping, self.TYPE_FIELD_GROUP, metadata.id)
    return groupRenderer.render(request,mapping,metadata,**kwargs)
  def renderField(self, request, mapping, metadata, **kwargs):
    metadata = self.checkMetadata(request, mapping, metadata)
    return """<div id=\""""+metadata.id+"""_field" class="pyWebMvcField">
              <div class="pyWebMvcLabel">
              """ + self.label(request, mapping, metadata.id) + """
              """ + self.instruction(request, mapping, metadata.id) + """
              </div><div class="pyWebMvcWidget">
              """ + self.widget(request, mapping, metadata.id, **kwargs) + """
              """ + self.renderErrors(request, mapping, metadata.id) + """
              </div>
              </div>"""
  def renderStart(self, request, mapping, metadata):
    if metadata.getLabel(request,mapping):
      legend = """<legend>%s</legend>""" % request.bundle[metadata.getLabel(request,mapping)]
    else:
      legend = ""
    return """<fieldset>""" +legend
  def renderEnd(self, request, mapping, metadata):
    return "</legend>"
  def render(self, request, mapping, metadata, **kwargs):
    return self.renderStart(request,mapping, metadata) + \
           self.renderFields(request,mapping, metadata, **kwargs) + \
           self.renderEnd(request,mapping,metadata)

class FormRenderer(FieldGroupRenderer):
  """Default form renderer creates a <div> based layout which can be styled
     with css."""
  def getMethod(self, request, mapping, method = None):
    if method is None and mapping.getFormMetadata(request):
      method = mapping.getFormMetadata(request).method
    return method
  def getType(self, request, mapping, type = None):
    if type is None and mapping.getFormMetadata(request):
      type = mapping.getFormMetadata(request).type
    return type
  def getAction(self, request, mapping, action = None):
    if action is None:
      action = mapping.getUrl()
    else:
      fwd = mapping.findForward(action)
      if fwd:
        action = mapping.findForward(action).getUrl()
    return action
  def getFormId(self, request, mapping):
    if mapping.getFormMetadata(request):
      return mapping.getFormMetadata(request).id
    else:
      return None
  def getOnSubmit(self, request, mapping):
    return None
  def renderStart(self, request, mapping, action, method):
    method = self.getMethod(request, mapping, method)
    type = self.getType(request, mapping, None)
    action = self.getAction(request, mapping, action)
    onSubmit = self.getOnSubmit(request, mapping)
    id = self.getFormId(request,mapping)
    form = "<form"
    if id:
      form += ' id="%s"' % id
    if action:
      form += ' action="%s"' % action
    if method:
      form += ' method="%s"' % method
    if type:
      form += ' enctype="%s"' % type
    if onSubmit:
      form += ' onsubmit="%s"' % onSubmit
    form += ">"
    #Some browsers (IE,Mozilla) will modify the value of this field to send
    #the charset of the submitted data
    form += '<input type="hidden" name="_charset_">'
    return form
  def renderEnd(self,request,mapping):
    return "</form>"
  def renderFocus(self,request, mapping, fieldId = None):
    if mapping.getFormMetadata(request) is None:
      return ""
    script = "<!-- No focus is set for this form -->"
    if fieldId is None:
      field = mapping.getFormMetadata(request).focus
    else:
      field = mapping.getFormMetadata(request).getFieldMetadata(fieldId)
    if field:
      if field.getType(request, mapping).input == "text":
        script = """<script type="text/javascript">
          var inputs = document.getElementsByTagName("INPUT");
          for (var f = 0; f < inputs.length; f++)
          {
            if (inputs[f].name == \""""+field.id+"""\")
            {
              try {
                inputs[f].focus();
              } catch (e) { }
              break;
            }
          }
        </script>"""
      else:
        script = "<!-- focus for the field type '"+field.getType(request, mapping).input+"' is not supported -->"
    return script
  def render(self, request, mapping, action = None, method = None, **kwargs):
    return self.renderStart(request, mapping, action, method) + \
           self.renderErrors(request, mapping,ActionError.GLOBAL) + \
           self.renderFields(request, mapping, **kwargs) + \
           self.renderEnd(request, mapping) + \
           self.renderFocus(request, mapping)


class TableFieldGroupRenderer(FieldGroupRenderer):
  def renderStart(self, request, mapping,metadata):
    return """<tbody>"""
  def renderEnd(self, request, mapping,metadata):
    return "</tbody>"
  def errors(self, request, mapping, name, colspan = 2):
    row = ""
    if self.hasError(request, mapping, name):
      row += '<tr class="pyWebMvcErrorRow"><td colspan="%i">' % (colspan)
      row += super(TableFieldGroupRenderer,self).errors(request, mapping, name)
      row += '</td></tr>'
    return row
  def renderField(self, request, mapping, fieldMetadata, widths = None,**kwargs):
    fieldMetadata = self.checkMetadata(request, mapping, fieldMetadata)
    name = fieldMetadata.id
    if kwargs.has_key("required"):
      required = kwargs["required"]
    else:
      required = None
    required = self.getRequired(request,mapping,name,required)
    if kwargs.has_key("display"):
      display = kwargs["display"]
    else:
      display = None
    display = self.getDisplay(request,mapping,name,display)
    typeMetadata = fieldMetadata.getType(request, mapping)
    if display == metadata.DISPLAY_HIDDEN:
      return '<tr class="pyWebMvcHiddenRow"><td colspan="2">'+self.widget(request, mapping, fieldMetadata.id, **kwargs)+"</td></tr>"
    rowClass = "pyWebMvcFieldRow"
    if fieldMetadata.hasAttribute("rowStyleClass"):
      rowClass += " "+fieldMetadata.getAttribute("rowStyleClass")
    rowOrientation = "horizontal"
    if fieldMetadata.hasAttribute("orient"):
      rowOrientation = fieldMetadata.getAttribute("orient")
      assert rowOrientation in ("horizontal","vertical")
    if typeMetadata.input == "checkbox":
      row = '<tr class="'+rowClass+'"><td valign="top" colspan="2"'
      if widths:
        width = 0
        if widths[0]: width += widths[0]
        if widths[1]: width += widths[1]
        row += ' width="%i"' % (width)
      row += '>'
      row += "<table style=\"margin:0; padding:0; margin-left:-2px\"> <tr> <td style=\"vertical-align: top;margin:0; margin-top: -2px; padding:0\">"
      row += self.widget(request, mapping, fieldMetadata.id, **kwargs)
      row += "</td><td style=\"vertical-align: top;margin:0; padding:0; padding-top:2px;\">"
      row += self.label(request, mapping, fieldMetadata.id, required=required, widgetDisplay=display, style="cursor: pointer")
      row += "</td><td style=\"vertical-align: top;margin:0; padding:0; padding-left:3px;\">"
      row += self.instruction(request, mapping, fieldMetadata.id, widgetDisplay=display)
      row += "</td></tr></table>"
      row += "</td></tr>"
    elif rowOrientation == "horizontal":
      row = '<tr class="'+rowClass+'">'
      row += '<td valign="top"'
      if widths and widths[0]:
        row += ' width="%i"' % (widths[0])
      row += '>'
      row += self.label(request, mapping, fieldMetadata.id, required=required, widgetDisplay=display)
      row += '</td><td valign="top"'
      if widths and widths[1]:
        row += ' width="%i"' % (widths[1])
      row += '>'
      row += """<table style="margin:0; padding:0;"> <tr>
      <td style="margin:0; padding:0;"> """
      row += self.widget(request, mapping, fieldMetadata.id, **kwargs)
      row += "</td>"
      instr = self.instruction(request, mapping, fieldMetadata.id, widgetDisplay=display)
      if not instr:
        instr = "&nbsp;"
      row += '<td style="margin:0; padding:0;" valign="top">%s</td>' % (instr)
      row += "</td></tr></table></td></tr>"
    elif rowOrientation == "vertical":
      instr = self.instruction(request, mapping, fieldMetadata.id, widgetDisplay=display)
      row = """
      <tr class="%(rowClass)s"><td colspan="3" %(width)s>
      <div class="pyWebMvcLabel">%(label)s</div>
      <div class="pyWebMvcWidget">%(widget)s</div>
      <div class="pyWebMvcInstruction">%(instr)s</div>
      </td></tr>
      """ % {
        "rowClass" : rowClass,
        "width" : (widths and ('width=%i' % (widths[0]+widths[1])) or ""),
        "label" : self.label(request, mapping, fieldMetadata.id, required=required, widgetDisplay=display),
        "widget":self.widget(request, mapping, fieldMetadata.id, **kwargs),
        "instr" : instr and instr or "&nbsp;",
      }
    row += self.errors(request, mapping, fieldMetadata.id)
    return row

class TableFormRenderer(FormRenderer,TableFieldGroupRenderer):
  def renderStart(self, request, mapping, action = None, method = None):
    return super(TableFormRenderer,self).renderStart( request, mapping, action, method) + \
           """<table class="pyWebMvcFormTable">"""
  def renderEnd(self, request, mapping):
    return "</table>" + \
           super(TableFormRenderer,self).renderEnd( request, mapping)
  def render(self, request, mapping, action = None, method = None, **kwargs):
    return super(TableFormRenderer,self).render( request, mapping, action, method, **kwargs)

