#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""The pywebmvc rendering framework."""

from pywebmvc.framework.util import PyWebMvcObject
from pywebmvc.framework import htmlutil

__all__ = [
            "factory",
            "form",
            "text",
            "widget",
          ]

class Renderer(PyWebMvcObject):
  """Base class for all Renderers."""
  TYPE_FORM="form"
  TYPE_FIELD_GROUP="fieldgroup"
  TYPE_FIELD_GROUP_LIST="fieldgrouplist"
  TYPE_FIELD="field"
  TYPE_SELECT="select"
  TYPE_SELECT_LIST="multiselect"
  TYPE_FILE="file"
  TYPE_FILE_LIST="filelist"
  TYPE_RADIO="radio"
  TYPE_RADIO_LIST="radiolist"
  TYPE_HIDDEN="hidden"
  TYPE_HIDDEN_LIST="hiddenlist"
  TYPE_TEXT="text"
  TYPE_TEXT_AREA="textarea"
  TYPE_TEXT_LIST="textlist"
  TYPE_PASSWORD="password"
  TYPE_PASSWORD_LIST="passwordlist"
  TYPE_READ_ONLY="readonly"
  TYPE_READ_ONLY_LIST="readonlylist"
  TYPE_LABEL="label"
  TYPE_INSTRUCTION="instruction"
  TYPE_REQUIRED="required"
  TYPE_ERRORS="errors"
  TYPE_ERROR="error"
  TYPE_CHECKBOX="checkbox"
  TYPE_SUBMIT="submit"
  TYPE_SUBMIT_LIST="submitlist"
  def getRenderer(self, req, mapping, type, name):
    return mapping.rendererFactory.getRenderer(type, req, mapping, name)
  def getIgnoreAttributes(self):
    return ["options","required"]
  def renderAttributes(self, map):
    html = ""
    ignore= self.getIgnoreAttributes()
    for key in map.keys():
      if not key in ignore:
        html += ' %s="%s"' % (key, htmlutil.escapeAttribute(map[key]))
    return html
  def render(self, request, mapping, *args, **kwargs):
    """All Subclasses must implement this method"""
    return ""

class NullRenderer(Renderer):
  def render(self, *args, **kwargs):
    return ""

class ListRenderer(Renderer):
  def __init__(self, type, before = "", after = "", separator = ""):
    self.type = type
    self.before = before
    self.after = after
    self.separator = separator
  def render(self, request, mapping, name, values, cssClass, **kwargs):
    elementRenderer = self.getRenderer(request, mapping, self.type, name)
    html = ""
    first = True
    for v in values:
      if first:
        first = False
      else:
        html += self.separator
      html += self.before + elementRenderer.render(request, mapping, name, v,
              cssClass, **kwargs) + self.after
    return html

class MutableListRenderer(Renderer):
  def __init__(self, type):
    self.type = type
  def render(self, request, mapping, name, values, cssClass, **kwargs):
    index = 0
    html = ""
    elementRenderer = self.getRenderer(request, mapping, self.type, name)
    for v in values:
      html += '<div style="white-space: nowrap">'
      html += elementRenderer.render(request, mapping, name, v,
                                     cssClass, **kwargs)
      html += '<span>'
      if len(values) > 1:
        html += '<button type="button" dontSubmit="true" onclick="delRow(this, event)">-</button>'
      if index + 1 == len(values):
        html += '<button type="button" dontSubmit="true" onclick="addRow(this, event)">+</button>'
      html += "</span></div>"
      index += 1
    return html

