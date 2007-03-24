#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
"""Group and access renderers abstractly."""

from types import *
from pywebmvc.framework import htmlutil, metadata
from pywebmvc.framework.util import PyWebMvcObject
from pywebmvc.framework.core import ActionError, PyWebMvcException
from pywebmvc.framework.metadata import FieldMetadata, MetadataGroup
from __init__ import Renderer
from form import *
from widget import *
from text import *


class RendererFactory(PyWebMvcObject):
  """Logically groups a set of renderers together. RendererFactories can be 
     associated to an action mapping to get different rendering behaviors
     for different actions"""
  def __init__(self):
    self.renderers = {}
    self.setRenderer(Renderer.TYPE_FORM,FormRenderer())
    self.setRenderer(Renderer.TYPE_FIELD_GROUP,FieldGroupRenderer())
    self.setRenderer(Renderer.TYPE_FIELD_GROUP_LIST,FieldGroupListRenderer())
    self.setRenderer(Renderer.TYPE_SELECT,SelectRenderer())
    self.setRenderer(Renderer.TYPE_SELECT_LIST,MultiSelectRenderer())
    self.setRenderer(Renderer.TYPE_RADIO,RadioRenderer())
    self.setRenderer(Renderer.TYPE_RADIO_LIST,RadioListRenderer())
    self.setRenderer(Renderer.TYPE_HIDDEN,HiddenRenderer())
    self.setRenderer(Renderer.TYPE_HIDDEN_LIST,HiddenRenderer())
    self.setRenderer(Renderer.TYPE_FILE,FileRenderer())
    self.setRenderer(Renderer.TYPE_TEXT,TextInputRenderer())
    self.setRenderer(Renderer.TYPE_TEXT_LIST,TextListRenderer())
    self.setRenderer(Renderer.TYPE_TEXT_AREA,TextAreaRenderer())
    self.setRenderer(Renderer.TYPE_PASSWORD,PasswordInputRenderer())
    self.setRenderer(Renderer.TYPE_PASSWORD_LIST,PasswordListRenderer())
    self.setRenderer(Renderer.TYPE_READ_ONLY,ReadOnlyRenderer())
    self.setRenderer(Renderer.TYPE_READ_ONLY_LIST,ReadOnlyListRenderer())
    self.setRenderer(Renderer.TYPE_LABEL,LabelRenderer())
    self.setRenderer(Renderer.TYPE_INSTRUCTION,InstructionRenderer())
    self.setRenderer(Renderer.TYPE_REQUIRED,RequiredRenderer())
    self.setRenderer(Renderer.TYPE_ERRORS,ErrorsRenderer())
    self.setRenderer(Renderer.TYPE_ERROR,ErrorRenderer())
    self.setRenderer(Renderer.TYPE_CHECKBOX,CheckboxRenderer())
    self.setRenderer(Renderer.TYPE_SUBMIT,SubmitRenderer())
    self.setRenderer(Renderer.TYPE_SUBMIT_LIST,SubmitListRenderer())
  def getFormRenderer(self, req, mapping):
    return self.getRenderer(Renderer.TYPE_FORM, req, mapping)
  def setRenderer(self,type,renderer):
    self.renderers[type] = renderer
  def getRenderer(self,type, req = None, mapping = None, name = None):
    renderer = None
    if mapping and req and mapping.getFormMetadata(req):
      if name:
        if mapping.getFormMetadata(req).hasMetadata(name):
          md = mapping.getFormMetadata(req).getMetadata(name)
        else:
          md = mapping.getFormMetadata(req)
      else:
        md = mapping.getFormMetadata(req)
      while md and not md.hasRenderer(type):
        md = md.parent
      if md:
        renderer = md.getRenderer(type)
    if renderer is None:
      renderer = self.renderers[type]
    return renderer

pyWebMvcDefaultRendererFactory = RendererFactory()
