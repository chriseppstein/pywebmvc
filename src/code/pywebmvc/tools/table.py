import math
from pywebmvc.framework.util import PyWebMvcObject
from pywebmvc.framework import htmlutil

class Pager(PyWebMvcObject):
  def getListSize(self,req):
    """This method must be overridden by the sub class"""
    return 0
  def __getListSize(self, req):
    attrName = "pagerListSizeFor" + self.__class__.__name__   # because we can have more than 1 pager per page
    if hasattr(req, attrName):
      return getattr(req, attrName)
    size = self.getListSize(req)
    setattr(req, attrName, size)
    return size
  def getStartIndex(self,req):
    """returns the inclusive start index"""
    startIndex = self.getCurrentPage(req)*self.__getCurrentPageSize(req)
    return min(self.__getListSize(req),startIndex)
  def getEndIndex(self,req):
    """returns the exclusive end index"""
    endIndex = self.getStartIndex(req)+self.__getCurrentPageSize(req)
    return min(self.__getListSize(req),endIndex)
  def getPageParamName(self):
    return "page"
  def getPageSize(self,req):
    return 25
  def getCurrentPage(self,req):
    if req.form.has_key(self.getPageParamName()):
      size = self.__getListSize(req) 
      pageSize = self.__getCurrentPageSize(req)
      numPages = int(math.ceil(float(size)/pageSize))
      if numPages == 0:
        return 0
      return min(numPages - 1, int(req.form[self.getPageParamName()]))
    else:
      return 0
  def getTypeString(self,req):
    return req.bundle["term.items"]
  def getPagerSummary(self,req):
    html = '<span class="pagerstatus">'
    size = self.__getListSize(req) 
    if size < self.__getCurrentPageSize(req):
      #str:ok
      html += req.bundle.getMessage("pywebmvc.tools.pager.message.allShown", str(size), self.getTypeString(req))
    else:
      #str:ok
      start = str(self.getStartIndex(req) + 1)
      #str:ok
      end = str(self.getEndIndex(req))
      #str:ok
      html += req.bundle.getMessage("pywebmvc.tools.pager.message.rangeShown", start, end, str(size), self.getTypeString(req))

    size = self.__getListSize(req)
    pageSize = self.__getCurrentPageSize(req)
    numPages = int(math.ceil(float(size)/pageSize))
    if numPages > 2:
      html += self.getGotoControl(req)
    html += '</span>'
    return html
  def getPageParams(self,req,exclude=[]):
    if req.form.has_key(self.getPageParamName()) and not (self.getPageParamName() in exclude):
      return [(self.getPageParamName(),req.form[self.getPageParamName()])]
    else:
      return []
  def getPager(self,req):
    size = self.__getListSize(req) 
    pageSize = self.__getCurrentPageSize(req)
    curPage = self.getCurrentPage(req)
    numPages = int(math.ceil(float(size)/pageSize))
    html = ""
    paramString = ""
    parameters = self.getPageParams(req,exclude=[self.getPageParamName()])
    if parameters:
      paramString = "&"+htmlutil.getParameterString(parameters)
    if size > pageSize: 
      html += '<div class="pager">'
      if curPage > 1:
        html += '<a href="?%s=0%s">&lt;&lt;</a>&nbsp;' % (self.getPageParamName(), paramString)
      if curPage > 0:
        html += '<a href="?%s=%i%s">&lt;</a>&nbsp;' % (self.getPageParamName(), curPage - 1, paramString)
      startPage = max(0,curPage -5)
      stopPage = min(max(curPage + 5, 10), numPages)
      if startPage > 0:
        html += "...&nbsp;"
      for i in range(startPage,stopPage):
        if i == curPage:
          html += '<span class="curPage">%i</span>&nbsp;' % (i+1)
        else:
          html += '<a href="?%s=%i%s">%i</a>&nbsp;' % (self.getPageParamName(), i,paramString,i+1)
      if stopPage < numPages - 1:
        html += "...&nbsp;"
      if curPage < numPages - 1:
        html += '<a href="?%s=%i%s">&gt;</a>&nbsp;' % (self.getPageParamName(), curPage + 1, paramString)
      if curPage < numPages - 2:
        html += '<a href="?%s=%i%s">&gt;&gt;</a>&nbsp;' % (self.getPageParamName(), numPages - 1, paramString)
      html += '</div>'
    return html
  def getPageSizeSelector(self, req):
    html = """ <select id="%s" onChange="submitPageSizeChangeRequest('%s', '%s');">\n""" % (self.getPageSizeAttrName(), self.getPageSizeAttrName(), self.getPageParamName())
    for size in self.getPageSizeList():
      selText = ""
      if self.__getCurrentPageSize(req) == size:
        selText = """ selected="selected" """
      html += """ <option value="%s" %s>%s</option>\n""" % (size, selText, size)
    html += "</select>\n"
    return html
  def __getCurrentPageSize(self, req):
    attrName = self.getPageSizeAttrName()
    if hasattr(req, attrName):
      return int(getattr(req, attrName))

    if req.form.has_key(attrName):
      curSize = req.form[attrName]
      req.session[attrName] = curSize
      req.session.save()
    elif req.session.has_key(attrName):
      curSize = req.session[attrName]
    else:
      curSize = self.getPageSize(req)
    setattr(req, attrName, curSize)
    return int(curSize)
  def getPageSizeAttrName(self):
    """ this name needs to unique across all pagers in the app since it is stored in the session """
    return "pageSizeFor" + self.__class__.__name__
  def getPageSizeList(self):
    return [25, 50, 100]
  def getGotoControl(self, req):
    html = """
       <input type="text"  id="gotoPageText" size="5" onkeypress="var RETURN_KEY = 13;  if(event.keyCode == RETURN_KEY) { handleGotoPage(%(page)d, %(size)d, '%(param)s');}"> </input> <button onclick="handleGotoPage(%(page)d, %(size)d, '%(param)s'); return false;"> Go to Range</button>
    """ % {"page" : self.__getCurrentPageSize(req), "size" : self.__getListSize(req), "param" : self.getPageParamName()}
    return html

class Column:
  def __init__(self, id, label, property, maxlength=None, width=None, formatter=None, primary=False, defaultOrder="asc", sortable=True, style=None, align=None):
    self.id=id
    self.label=label
    self.property=property
    self.maxlength=maxlength
    self.width=width
    self.formatter=formatter
    self.primary=primary
    self.defaultOrder=defaultOrder
    self.align=align
    self.sortable=sortable
    self.style=style

class Table(Pager):
  def __init__(self, klass, rowHighlighting=True):
    self.klass = klass
    self.rowHighlighting = rowHighlighting
  def getSortOrder(self, req, column):
    if req.form.has_key(self.getSortOrderParam()) and req.form[self.getSortOrderParam()] in ("asc", "desc"):
      return req.form[self.getSortOrderParam()]
    else:
      return column.defaultOrder
  def getSortOrderParam(self):
    return "sortOrder"
  def getOrderByParam(self):
    return "orderBy"
  def getSortColumn(self,req,columns):
    if req.form.has_key(self.getOrderByParam()):
      for col in columns:
        if req.form[self.getOrderByParam()] == col.id:
          return col
    for col in columns:
      if col.primary and col.sortable:
        return col
    return None
  def getRowClass(self, req, index, item):
    if index % 2 == 0:
      return "even"
    else:
      return "odd"
  def getCellMarkup(self, req, item, column):
    return ("", "")
  def getForeignParams(self):
    return []
  def getParamNames(self):
    return [self.getOrderByParam(), self.getSortOrderParam(), self.getPageParamName()] + self.getForeignParams()
  def getPageParams(self,req,exclude=[]):
    params = super(Table, self).getPageParams(req,exclude)
    for paramName in [self.getOrderByParam(), self.getSortOrderParam()] + self.getForeignParams():
      if req.form.has_key(paramName) and not (paramName in exclude):
        params += [(paramName, req.form[paramName])]
    return params
  def getCellValue(self, req, item, column):
    try:
      value = eval("item.%s" % column.property)
    except AttributeError:
      value = ""
    if column.formatter:
      cellText = column.formatter(req, item, value)
    else:
      cellText = unicode(value)
    return cellText
  def getTable(self, req):
    return """\n\n<div class="pyWebMvcWholeTable">\n""" + self.displayHeaderArea(req) +  self.displayTableContents(req) + self.getPager(req) + "\n</div>\n"
  def displayHeaderArea(self, req):
    return '<div class="pagersummary">'+self.getPagerSummary(req)+'</div>'
  def displayTableContents(self, req):
    list = '<table class="%s" cellspacing="0" border="0" cellpadding="0">' % (self.klass)
    list += '<thead><tr>'
    columns = self.getColumns(req)
    sortCol = self.getSortColumn(req,columns)
    if sortCol:
      sortOrder = self.getSortOrder(req, sortCol)
    else:
      sortOrder = None
    for column in columns:
      th = '<th'
      if column.width:
        th += ' width="%s"' % (column.width)
      if sortCol and column.id == sortCol.id:
        th += ' class="selected"'
      if column.style:
        th += ' style="%s"' % (column.style)
      th += '>'
      if sortCol and column.id == sortCol.id:
        if sortOrder == "asc":
          dir = "desc"
          klass = "asc"
          msg = "(%s)" % req.bundle["pywebmvc.common.ascending"]
        else:
          dir = "asc"
          klass = "desc"
          msg = "(%s)" % req.bundle["pywebmvc.common.descending"]
        params = self.getPageParams(req, exclude=[self.getSortOrderParam(), self.getOrderByParam()])
        params += [(self.getSortOrderParam(), dir), (self.getOrderByParam(), column.id)]
        paramStr = htmlutil.getParameterString(params)
        th += '<div class="sorted">%s</div>' % (req.bundle[column.label])
        th += '<a href="?%s" class="%s"><span>%s</span>&nbsp;</a>' % (paramStr, klass, msg)
      else:
        params = self.getPageParams(req, exclude=[self.getSortOrderParam(), self.getOrderByParam()])
        params += [(self.getOrderByParam(), column.id)]
        paramStr = htmlutil.getParameterString(params)
        if column.sortable:
          th += '<a href="?%s" class="sortable">%s</a>' % (
            paramStr, req.bundle[column.label])
        else:
          th += req.bundle[column.label]
      th += '</th>'
      list += th
    list += '</tr></thead>'
    list += '<tbody>'
    index = 0
    items = self.getItems(req,sortCol,sortOrder,self.getStartIndex(req),self.getEndIndex(req))
    if items:
      for item in items:
        list += self._generateCellRow(req, index, item, columns)
        index += 1
    else:
      list += '<tr><td colspan="%i">%s</td></tr>' % (
        len(columns),
        req.bundle.getMessage("pywebmvc.tools.table.message.emptyList", self.getTypeString(req)))
    list += self.bottomOfTableHook(req)
    list += '</tbody></table>'
    return list
  def getCellRowEventHandlers(self, req, index, item, rowClass):
    if self.rowHighlighting:
      handlers = {"onmouseover" : "this.className = 'hovered'",
                "onmouseout" : "this.className = '%s'" % rowClass}
    else:
      handlers = {}
    return handlers
  def _generateCellRow(self, req, index, item, columns):
    rowClass = self.getRowClass(req, index, item)
    tr = """<tr class="%s\"""" % (rowClass)
    handlers = self.getCellRowEventHandlers(req, index, item, rowClass)
    for key in handlers.keys():
      tr += """ %s="%s\"""" % (key, handlers[key])
    tr += ">"
    for column in columns:
      cellText = self.getCellValue(req, item, column)
      if column.maxlength:
        cellText = self.doTruncate(cellText, column.maxlength)
      attrs = ""
      if column.align:
        attrs = ' style="text-align: %s;"' % column.align
      if column.style:
        attrs = ' style="%s"' % (column.style)
      (markupStart, markupEnd) = self.getCellMarkup(req, item, column)
      tr += '<td%s>%s%s%s</td>' % (attrs, markupStart, cellText, markupEnd)
    tr += '</tr>'
    return tr
  def bottomOfTableHook(self, req):
    return ""
  def doTruncate(self, cellText, length):
    return htmlutil.truncateText(cellText, length)
