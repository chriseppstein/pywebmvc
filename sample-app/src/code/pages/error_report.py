#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
import traceback, os, string
import pywebmvc.framework.htmlutil as htmlutil
from  pywebmvc.framework.core import HtmlPage

class ErrorReportBasePage(HtmlPage):
  def getTitle(self, req, mapping):
    return "Error"

class ErrorReportPage(ErrorReportBasePage):
  def getBodyStart(self, req,mapping):
    stacktrace = ""
    formData = ""
    if req.err_headers_out.has_key("EXCEPTION"):
      stacktrace = req.err_headers_out["EXCEPTION"]
      formData = req.err_headers_out["FORMDATA"]
    return ErrorReportBasePage.getBodyStart(self,req,mapping) + """
    <div style="width: 100%;">
  <pre id="tbDisplay" style="width: 100%; display:block">
===STACK TRACE===
"""+htmlutil.escapeHtml(stacktrace)+"""
===FORM DATA===
"""+htmlutil.escapeHtml(formData)+"""
  </pre>
  </div>
"""
