#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
from mod_python import apache, util
from pywebmvc.framework.util import PyWebMvcObject
from pywebmvc.framework.apache import ActionHandler
from pages.error_report import ErrorReportPage

forms = None
types = None


class ErrorHandler(PyWebMvcObject):
  def __init__(self):
    pass
  def __call__(self, req):
    ah = ActionHandler()
    req.locale = ah.getRequestLocale(req)
    req.bundle = ah.getBundle(req)
    req.form = util.FieldStorage(req,1,False)
    try:
      if req.err_headers_out.has_key("EXCEPTION"):
        msg = req.err_headers_out["EXCEPTION"]
      else:
        msg = "Unknown Error!! Please review the apache and aca logs."
      summary = "Error details unavailable: Stack trace couldn't be parsed."
      lastLine = msg.split('\n')[-2:-1]
      if lastLine:
        lastLine = lastLine[0]
        if lastLine:
          summary = lastLine
    except:
      raise
    response = ErrorReportPage().render(req,None)
    req.content_type = "text/html; charset=utf-8"
    if req.err_headers_out.has_key("EXCEPTION"):
      req.err_headers_out["EXCEPTION"] = ""
      req.err_headers_out["FORMDATA"] = ""
    req.set_content_length(len(response))
    req.send_http_header()
    req.write(response)
    return apache.OK

handler = ErrorHandler()
