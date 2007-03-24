from backend.model import AddressBookItem
from backend import *
from pywebmvc import *

addressBookHandler = ActionHandler()

class AddressBookAction(Action):
  def __call__(self,req,mapping):
    return mapping["self"]

class AddressBookPage(HtmlPage):
  def __init__(self):
    self.searchTool = AddressSearchTool()
    self.table = AddressBookTable(self.searchTool)
  def getTitle(self, req, mapping):
    return req.bundle["title.addressBook"]
  def getStylesheets(self, req, mapping):
    return super(AddressBookPage,self).getStylesheets(req, mapping)+["/pywebmvc-data/style/pywebmvc.css", "/style/main.css"]
  def getScripts(self, req, mapping):
    return ['/pywebmvc-data/script/searchtool.js'] + super(AddressBookPage, self).getScripts(req, mapping)
  def getBodyStart(self,req,mapping):
    return super(AddressBookPage, self).getBodyStart(req, mapping) + self.searchTool.renderHtml(req, mapping) + """
       <div id="editlink"> <a href="%s"> Add a Contact </a> </div>
    """ % (href(req, "addressEntry")) + self.table.getTable(req)

class AddressBookTable(Table):
  def __init__(self, searchTool):
    Table.__init__(self, "list")
    self.searchTool = searchTool
  def getTypeString(self,req):
    return req.bundle["term.entries"]
  def getListSize(self, req):
    return getBackend(req).getAddressBookHome().getLength()
  def getItems(self, req, sortColumn, sortOrder, startIndex, endIndex):
    searchCriteria = self.searchTool.getSearchCriteria(req)
    return getBackend(req).getAddressBookHome().find(searchCriteria, sortColumn, sortOrder)
  def getColumns(self, req):
    def commandsFormatter(req, item, dummy):
      return """ <button onclick="location.href='%s?id=%s'; return false"> Edit </button> """ % (href(req, "addressEntry"), item.id)
    return [
      Column("firstName", "header.addressBook.firstName", "firstName", None, "10%", defaultOrder="asc", primary=True),
      Column("lastName", "header.addressBook.lastName", "lastName", None, "10%", defaultOrder="asc"),
      Column("street", "header.addressBook.street", "street", None, "30%", defaultOrder="asc"),
      Column("city", "header.addressBook.city", "city", None, "10%", defaultOrder="asc"),
      Column("state", "header.addressBook.state", "state", None, "10%", defaultOrder="asc"),
      Column("phone", "header.addressBook.phone", "phone", None, "10%", defaultOrder="asc"),
      Column("email", "header.addressBook.email", "email", None, "10%", defaultOrder="asc"),
      Column("commands", "header.addressBook.commands", "commands", None, "10%", commandsFormatter, sortable=False),
      ]
  def getPageParams(self,req,exclude=[]):
    params = super(Table, self).getPageParams(req, exclude)
    eventParamList = self.searchTool.getParams()
    for evParam in eventParamList:
      if req.form.has_key(evParam):
        params.append((evParam, req.form[evParam]))
    return params
  def displayHeaderArea(self, req):
    return '<div class="pagersummary">%s</div>' % (getTwoSectionHeader(self.searchTool.getLastSearchDescription(req), self.getPagerSummary(req)))


class AddressEntryAction(Action):
  def __call__(self,req,mapping):
    # do an add
    if req.form.has_key("do"):
      if req.form["do"] == "save":
        req.errors = validateForm(req,mapping)
        if req.errors:
          req.log_error("validation error")
          return mapping["self"]
        addressBookItem = transferToEntity(req.form, mapping.formMetadata)
        req.log_error(repr(addressBookItem))
        getBackend(req).getAddressBookHome().save(addressBookItem)
        return mapping["success"]
      else:
        return mapping["cancel"]

    # do an edit
    if req.form.has_key("id"):
      addressBookItem = getBackend(req).getAddressBookHome().findById(req.form["id"])
      transferToForm(addressBookItem, req.form, mapping.formMetadata)
      return mapping["self"]

    # otherwise show blank form
    return mapping["self"]


class AddressEntryPage(HtmlPage):
  def getTitle(self, req, mapping):
    return req.bundle["title.addressEntry"]
  def getStylesheets(self, req, mapping):
    return super(AddressEntryPage,self).getStylesheets(req, mapping)+["/pywebmvc-data/style/pywebmvc.css", "/style/main.css"]
  def getBodyStart(self,req,mapping):
    formRenderer = mapping.rendererFactory.getFormRenderer(mapping)
    return super(AddressEntryPage, self).getBodyStart(req, mapping) + formRenderer.render(req, mapping)

class AddressSearchTool(SearchTool):
  def getFilters(self):
    return [FirstNameFilter(), LastNameFilter(), StreetFilter(), CityFilter(), StateFilter(), PhoneNumberFilter(), EmailFilter()] 
  def getItemName(self, req):
    return req.bundle["term.entries"]

class FirstNameFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "firstName"
  def getQueryParam(self):
    return "firstName"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.firstName"]
  def getItemText(self):
    return "with first name like"

class LastNameFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "lastName"
  def getQueryParam(self):
    return "lastName"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.lastName"]
  def getItemText(self):
    return "with last name like"

class StreetFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "street"
  def getQueryParam(self):
    return "street"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.street"]
  def getItemText(self):
    return "with street like"

class CityFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "city"
  def getQueryParam(self):
    return "city"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.city"]
  def getItemText(self):
    return "with city like"

class StateFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "state"
  def getQueryParam(self):
    return "state"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.state"]
  def getItemText(self):
    return "with state like"

class PhoneNumberFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "phone"
  def getQueryParam(self):
    return "phone"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.phone"]
  def getItemText(self):
    return "with phone number like"

class EmailFilter(SubstringMatchTextFilter):
  def getModelProperty(self):
    return "email"
  def getQueryParam(self):
    return "email"
  def getButtonName(self, req):
    return req.bundle["header.addressBook.email"]
  def getItemText(self):
    return "with email like"

def getTwoSectionHeader(leftSide, rightSide):
  return """
<div style="float: left;"> %s </div>
<div style="text-align: right"> %s </div>
    """ % (leftSide, rightSide)

