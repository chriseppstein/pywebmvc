#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 
from pywebmvc.tools.dbutils import SearchCriteria, BasicSearchCriteria, AndSearchCriteria, OrSearchCriteria, InSearchCriteria
from datetime import datetime
import string

def escapeJsString(aString):
  aString = string.replace(aString, "'", "\\'")
  aString = string.replace(aString, '"', '\\"')
  return aString


class Filter:
  def getModelAndControllerJavascript(self, req, mapping):
    pass

  def getWidgets(self, req, mapping):
    html = """
    <div>
       <button %s onclick="%s.handleMainButton(); return false" type="normal">%s</button>
    </div>
    <div style="position: relative">
    <div id="%sPopupForm" style="display:none;width:%s" class="searchFormPopup">
       <form onsubmit="%s.handleOK(); return false" style="margin:0; padding: 0">
       <div>
       %s
       </div>
       <div>
          <button id="%sFilterOKButton" onclick="%s.handleOK(); return false;"> OK </button>
          <button id="%sFilterCancelButton" onclick="%s.handleCancel(); return false;"> Cancel </button>
       </div>
       </form>
    </div>
    </div>
    """ % (self.__getMouseover(req), self.getControllerName(), self.getButtonName(req), self.getName(), self.getPopupWidth(), self.getControllerName(), self.getPopupContents(req), self.getName(), self.getControllerName(), self.getName(), self.getControllerName())
    return html
  def getControllerName(self):
    return "document.%sController" % (self.getName())
  def getModelObjectName(self):
    return "document.%sModelObject" % (self.getName())
  def getName(self):
    return self.__class__.__name__
  def getPopupContents(self, req):
    raise "please override"
  def getPopupWidth(self):
    return "auto"
  def getQueryParam(self):
    raise "please override"
  def getSearchCriteria(self,req):
    raise "please override"
  def getButtonName(self, req):
    raise "please override"
  def __getMouseover(self, req):
    mouseoverJS = self.getMouseoverJS(req)
    return mouseoverJS and """onmouseover="%s" """ % (mouseoverJS) or ""
  def getMouseoverJS(self, req):
    return None
  

class SearchTool(object):
  def renderHtml(self, req, mapping):
    filterList = self.getFilters()
    html = self.renderControls(req, mapping, filterList)
    html += """<script>
       document.searchModelList = [];
    """
    for filt in filterList:
      html += filt.getModelAndControllerJavascript(req, mapping)
      html += """ document.searchModelList.push(%s)\n""" % filt.getModelObjectName()
      if req.form.has_key(filt.getQueryParam()):
        html += """ %s.initializeFromURLValue("%s")\n""" % (filt.getModelObjectName(), req.form[filt.getQueryParam()])
    html += "\n</script>\n"
    html += self.getControllerJavascript(req, mapping);
    return html

  def renderControls(self, req, mapping, filterList):
    html = """
    <table cellspacing="0" cellpadding="0"> <tr>
    """
    for filt in filterList:
      html += """ <td style="padding-right: 10px"> %s </td> """ % filt.getWidgets(req, mapping)
    html += """ </tr> </table>
    <div style="margin-top:10px">  %s </div>

    """ % self.getSearchTextLine(req, mapping)
    return html

  def getLastSearchDescription(self, req):
    return """<div id="staticSearch"> %s </div>
    <script>
       if(document.searchController) {
          document.searchController.displayInitialValues();
       }
    </script>
    """ % (req.bundle["pywebmvc.tools.searchtool.noquery"])

  def getFilters(self):
    raise "not implemeneted"

  def getControllerJavascript(self, req, mapping):
    html = """
    <script>
       document.searchController = new %s("%s", document.searchModelList, "%s");
       document.searchController.displayInitialValues();
    </script>
    """ % (self.getControllerName(req), self.getItemName(req), self.getResetParam())
    return html
  def getControllerName(self, req):
    return "SearchController"
  def getResetParam(self):
    return "searchToolReset"
    

  def getSearchTextLine(self, req, mapping):
    html = """
      <form style="margin:0; padding: 0">
      <span id="searchDefaultText" style="display:none"> %s </span>
      <button id="searchResetButton" onclick="document.searchController.handleReset(); return false" disabled> Reset </button>
      </form>
      """ % (self.getDefaultText(req))
    return html
  def getDefaultText(self, req):
    return "%s %s" % (req.bundle["pywebmvc.tools.searchtool.defaulttext"], self.getItemName(req))

  def getItemName(self, req):
    raise "not implemeneted"

  def getSearchCriteria(self, req):
    searchCriteria = None
    for filt in self.getFilters():
      param = filt.getQueryParam()
      if req.form.has_key(param):
        curCriteria = filt.getSearchCriteria(req)
        if searchCriteria:
          searchCriteria = AndSearchCriteria(searchCriteria, curCriteria)
        else:
          searchCriteria = curCriteria
    return searchCriteria
  
  def getParams(self):
    params = []
    for filt in self.getFilters():
      params.append(filt.getQueryParam())
    return params

def gmtStampToSQLLocal(stamp):
  date = datetime.fromtimestamp(int(stamp) / 1000)
  return date.isoformat(" ")

class TimeFilter(Filter):
  def getModelAndControllerJavascript(self, req, mapping):
    javascript = """
    function %(name)sModel (){
    }

    %(name)sModel.timeText = {
       "1"    : "%(hour)s",
       "2"    : "%(2hours)s",
       "4"    : "%(4hours)s",
       "8"    : "%(8hours)s",
       "12"   : "%(12hours)s",
       "day"  : "%(day)s",
       "week" : "%(week)s"
    };

    %(name)sModel.timeMilliseconds = {
       "1"    : 1000 * 60 * 60,
       "2"    : 2000 * 60 * 60,
       "4"    : 4000 * 60 * 60,
       "8"    : 8000 * 60 * 60,
       "12"   : 12000 * 60 * 60,
       "day"  : 24000 * 60 * 60,
       "week" : 7 * 24000 * 60 * 60
    }
       
    %(name)sModel.prototype = new BasicModel(["mode", "recentCode", "startTime", "endTime"], "%(queryParam)s", "%(name)s");

    %(name)sModel.prototype.isEmpty = function () {
       return !this.mode || this.mode == "none";
    }

    %(name)sModel.prototype.clear = function () {
       return this.mode = "none";
    }

    %(name)sModel.prototype.getSearchText = function() {
       if (this.mode == "latest") 
          return "%(timeName)s from the last <b>" + %(name)sModel.timeText[this.recentCode] + "</b>";
       else {
          return "%(timeName)s from <b>" + jsDateToSQLLocal(this.startTime) + "</b> to <b>" + jsDateToSQLLocal(this.endTime) + "</b>";
       }
    }

    %(name)sModel.prototype.getURLValue = function() {
       if (this.mode == "latest") {
          var end = new Date();
          var start = new Date(end.getTime() - %(name)sModel.timeMilliseconds[this.recentCode]);
          return String(start.getTime()) + "," + String(end.getTime());
       }
       return String(this.startTime.getTime()) + "," + String(this.endTime.getTime());
    }
    %(name)sModel.prototype.initializeFromURLValue = function(urlValue) {
       var times = urlValue.split(",")
       this.startTime = new Date(parseInt(times[0]));
       this.endTime = new Date(parseInt(times[1]));
       this.mode = "interval";
    }

    
    %(modelObject)s = new %(name)sModel();
    """ % {"name" : self.getName(), "queryParam" : self.getQueryParam(), "modelObject" : self.getModelObjectName(), "timeName" : self.getTimeName(req), "hour" : req.bundle["pywebmvc.tools.filters.time.message.hour"], "2hours" : req.bundle["pywebmvc.tools.filters.time.message.2hours"], "4hours" : req.bundle["pywebmvc.tools.filters.time.message.4hours"], "8hours" : req.bundle["pywebmvc.tools.filters.time.message.8hours"], "12hours" : req.bundle["pywebmvc.tools.filters.time.message.12hours"], "day" : req.bundle["pywebmvc.tools.filters.time.message.day"], "week" : req.bundle["pywebmvc.tools.filters.time.message.week"]}

    javascript += """
    function %(name)sController() {
       var base = "%(name)s";
       this.noneRadio = document.getElementById(base + "NoneRadio");
       this.latestRadio = document.getElementById(base + "LatestRadio");
       this.intervalRadio = document.getElementById(base + "IntervalRadio");
       this.latestSelect = document.getElementById(base + "Latest")
       this.startMonth = document.getElementById(base + "StartMonth")
       this.endMonth = document.getElementById(base + "EndMonth");
       this.startDay = document.getElementById(base + "StartDay")
       this.endDay = document.getElementById(base + "EndDay");
       this.startYear = document.getElementById(base + "StartYear")
       this.endYear = document.getElementById(base + "EndYear");
       this.startTime = document.getElementById(base + "StartTime")
       this.endTime = document.getElementById(base + "EndTime");
    }

    %(name)sController.prototype = new FilterController("%(name)s", %(modelObject)s);

    %(name)sController.prototype.handleModeChange = function(mode) {
       this.latestSelect.disabled = true;
       this.startMonth.disabled = true;
       this.endMonth.disabled = true;
       this.startDay.disabled = true;
       this.endDay.disabled = true;
       this.startYear.disabled = true;
       this.endYear.disabled = true;
       this.startTime.disabled = true;
       this.endTime.disabled = true;
       this.noneRadio.checked = false;
       this.latestRadio.checked = false;
       this.intervalRadio.checked = false;

       if (mode == "latest") {
          this.latestSelect.disabled = false;
          this.latestRadio.checked = true;
       }
       else if (mode == "interval") {
          this.startMonth.disabled = false;
          this.endMonth.disabled = false;
          this.startDay.disabled = false;
          this.endDay.disabled = false;
          this.startYear.disabled = false;
          this.endYear.disabled = false;
          this.startTime.disabled = false;
          this.endTime.disabled = false;
          this.intervalRadio.checked = true;
       } else {
          this.noneRadio.checked = true;
       }       
    }
    
    %(name)sController.prototype.doOK = function() {
       var dataObj;
       if(this.noneRadio.checked)
          dataObj = {"mode" : "none"}
       else if(this.latestRadio.checked)
          dataObj = {"mode" : "latest", "recentCode" : this.latestSelect.options[this.latestSelect.selectedIndex].value};
       else
       dataObj = {"mode" : "interval", "startTime" : this.makeTimeFromSelect("start"), "endTime" : this.makeTimeFromSelect("end")}
       document.searchController.addToSearch("%(name)s", dataObj)
    }

    %(name)sController.prototype.makeTimeFromSelect = function(s) {
       return new Date(this.selVal(s, "Year"), this.selVal(s, "Month") - 1, this.selVal(s, "Day"), this.selVal(s, "Time"));
    }

    %(name)sController.prototype.selVal = function(s, type) {
       var select = this[s + type];
       return select.options[select.selectedIndex].value;
    }

    %(name)sController.prototype.clear = function() {
       this.noneRadio.checked = true;
       this.handleModeChange("none")
    }
    
    %(name)sController.prototype.populateControls = function() {
       if(this.model.mode)
          this.handleModeChange(this.model.mode);
       if(this.model.mode == "latest") {
          setSelectTo(this.latestSelect, this.model.recentCode)
       }
       if(this.model.mode == "interval") {
          this.populateTimeSelects("start", this.model.startTime);
          this.populateTimeSelects("end",   this.model.endTime);
       }
    }

    %(name)sController.prototype.populateTimeSelects = function(name, date) {
       setSelectTo(this[name + "Year"],  String(date.getFullYear()));
       setSelectTo(this[name + "Month"], zeroPad(date.getMonth() + 1));
       setSelectTo(this[name + "Day"],   zeroPad(date.getDate()));
       setSelectTo(this[name + "Time"],  zeroPad(date.getHours()));
    }
    
    %(controllerName)s = new %(name)sController()
    """ % {"name" : self.getName(), "modelObject" : self.getModelObjectName(), "controllerName" : self.getControllerName()}
    return javascript;

  def getPopupContents(self, req):
    return """
        <table>
           <tr> <td style="vertical-align:top"> All </td> <td> <input id="%(name)sNoneRadio" type="radio" onclick="%(controller)s.handleModeChange('none')" checked> </input> </td> <td> &nbsp; </td> </tr>
           <tr> <td style="vertical-align:top"> Last </td> <td> <input id="%(name)sLatestRadio" type="radio" onclick="%(controller)s.handleModeChange('latest')"> </input> </td> 
                <td> <select id="%(name)sLatest" disabled>
                    <option value="1"> %(1hour)s </option>
                    <option value="2"> %(2hours)s </option>
                    <option value="4"> %(4hours)s </option>
                    <option value="8"> %(8hours)s </option>
                    <option value="12"> %(12hours)s </option>
                    <option value="day"> %(day)s </option>
                    <option value="week"> %(week)s </option>
                    </select> </td> </tr>
           <tr> <td style="vertical-align:top"> Interval </td> <td style="vertical-align:top"> <input id="%(name)sIntervalRadio" type="radio" onclick="%(controller)s.handleModeChange('interval')"> </input> </td> </tr> </table>
           <div>%(timeSelects)s </div>
        """ % {"name" : self.getName(), "controller" : self.getControllerName(), "timeSelects" : self.getTimeSelects(req), "1hour" : req.bundle["pywebmvc.tools.filters.time.select.1hour"], "2hours" : req.bundle["pywebmvc.tools.filters.time.select.2hours"], "4hours" : req.bundle["pywebmvc.tools.filters.time.select.4hours"], "8hours" : req.bundle["pywebmvc.tools.filters.time.select.8hours"], "12hours" : req.bundle["pywebmvc.tools.filters.time.select.12hours"], "day" : req.bundle["pywebmvc.tools.filters.time.select.day"], "week" : req.bundle["pywebmvc.tools.filters.time.select.week"]}
  def getTimeSelects(self, req):
    return """
    <table>
       <tr> <td> %s </td> %s </tr>
       <tr> <td> %s </td> %s </tr>
    </table> """ % (req.bundle["pywebmvc.tools.filters.time.select.start"], self.getSelectRow(req, "Start"),
                    req.bundle["pywebmvc.tools.filters.time.select.end"], self.getSelectRow(req, "End"))
  def getSelectRow(self, req, selname):
    return """ <td> %s </td> <td> %s </td> <td> %s </td> <td> %s </td>""" % (self.getMonthSelect(req, selname), self.getDaySelect(selname),
                                                                             self.getYearSelect(selname), self.getTimeSelect(selname))
  def getMonthSelect(self, req, selname):
    monthNames = [req.bundle["pywebmvc.tools.filters.time.jan"], req.bundle["pywebmvc.tools.filters.time.feb"], req.bundle["pywebmvc.tools.filters.time.mar"],
                  req.bundle["pywebmvc.tools.filters.time.apr"], req.bundle["pywebmvc.tools.filters.time.may"], req.bundle["pywebmvc.tools.filters.time.jun"],
                  req.bundle["pywebmvc.tools.filters.time.jul"], req.bundle["pywebmvc.tools.filters.time.aug"], req.bundle["pywebmvc.tools.filters.time.sep"],
                  req.bundle["pywebmvc.tools.filters.time.oct"], req.bundle["pywebmvc.tools.filters.time.nov"], req.bundle["pywebmvc.tools.filters.time.dec"]]
    curMonth = datetime.now().month
    html = """ <select id="%(monthSelect)s" disabled>\n """ % {"monthSelect" : self.getName() + selname + "Month"}
    for month in range(1, 13):
      html += """ <option value="%02d" %s> %s </option> """ % (month, month == curMonth and "selected=\"selected\"" or "", monthNames[month-1])
    html += """ </select> """
    return html
  def getDaySelect(self, selname):
    curDay = datetime.now().day
    result = """ <select id="%s" disabled>\n """ % (self.getName() + selname + "Day")
    for day in range(1, 32):
      valStr = "%02d" % day
      result += """ <option value="%s" %s> %s </option>\n""" % (valStr, curDay == day and "selected=\"selected\"" or "", valStr)
    return result + "</select>\n"
  def getYearSelect(self, selname):
    result = """ <select id="%s" disabled>\n """ % (self.getName() + selname + "Year")
    currentYear = datetime.now().year
    for year in range(2005, 2016):
      result += """ <option value="%s" %s> %s </option>\n""" % (year, year == currentYear and "selected=\"selected\"" or "", year)
    return result + "</select>\n"
  def getTimeSelect(self, selname):
    result = """ <select id="%s" disabled>\n """ % (self.getName() + selname + "Time")
    curHour = datetime.now().hour
    for time in range(0, 24):
      valStr = "%02d" % time
      dispStr = "%02d:00" % time
      result += """ <option value="%s" %s> %s </option>\n""" % (valStr, time == curHour and "selected=\"selected\"" or "", dispStr)
    return result + "</select>\n"
  def getPopupWidth(self):
    return "300px"
  def getSearchCriteria(self, req):
    (startTimeGMTTS,endTimeGMTTS) = req.form[self.getQueryParam()].split(",")
    startCrit = BasicSearchCriteria(self.getModelProperty(), BasicSearchCriteria.OP_GREATER_THAN_OR_EQUAL, gmtStampToSQLLocal(startTimeGMTTS))
    endCrit = BasicSearchCriteria(self.getModelProperty(), BasicSearchCriteria.OP_LESS_THAN_OR_EQUAL, gmtStampToSQLLocal(endTimeGMTTS))
    return AndSearchCriteria(startCrit, endCrit)
  def getTimeName(self, req):
    return ""
  

class SelectBoxFilter(Filter):
  def getModelAndControllerJavascript(self, req, mapping):
    javascript = """
    function %sModel (){
       this.select = -1;
       this.transTable = %s;
    }
    """ % (self.getName(), self.makeSelectLookupTable(req))

    javascript += """
    %(name)sModel.prototype = new BasicModel(["select"], "%(queryParam)s", "%(name)s");
    %(name)sModel.prototype.getSearchText = function() {
       return "%(itemText)s <b>" + this.transTable[this.select] + "</b>";
    }
    %(name)sModel.prototype.initializeFromURLValue = function(urlValue) {
       this.select = urlValue;
    }
    %(name)sModel.prototype.isEmpty = function() {
       return(this.select == -1);
    }
    %(name)sModel.prototype.clear = function() {
       this.select = -1;
    }
    %(modelObject)s = new %(name)sModel();
    """ % {"queryParam" : self.getQueryParam(), "name" : self.getName(), "modelObject" : self.getModelObjectName(), "itemText" : self.getItemText()}

    javascript += """
    function %(name)sController() {
       this.selectControl = document.getElementById("%(name)sData");
    }

    %(name)sController.prototype = new FilterController("%(name)s", %(modelObject)s);
    
    %(name)sController.prototype.doOK = function() {
       var selectValue = this.selectControl.options[this.selectControl.selectedIndex].value;
       document.searchController.addToSearch("%(name)s", {"select" : selectValue});
    }

    %(name)sController.prototype.clear = function() {
       this.selectControl.selectedIndex = 0;
    }
    %(name)sController.prototype.populateControls = function () {
       if(this.model.select)
          setSelectTo(this.selectControl, this.model.select);
    }
    %(controllerName)s = new %(name)sController();
    """ % {"name" : self.getName(), "modelObject" : self.getModelObjectName(), "controllerName" : self.getControllerName()}
    return javascript
  def getPopupContents(self, req):
    html =  """ <select id="%sData" name="%sDataName"> \n""" % (self.getName(), self.getName())
    html += """ <option value="-1"> %s </option> \n""" % (req.bundle["pywebmvc.tools.filters.selectbox.any"])
    for pair in self.getSelectContents(req):
      html += """ <option value="%s"> %s </option> """ % ( pair[0], pair[1])
    html += """ </select> \n"""
    return html
  def makeSelectLookupTable(self, req):
    lookupTable = {}
    transTable = "{"
    first = True
    for pair in self.getSelectContents(req):
      if first:
        sep = ""
        first = False
      else:
        sep = ","
      transTable += "%s\n\"%s\" : \"%s\"" % (sep,escapeJsString(pair[0]),escapeJsString(pair[1].encode("unicode_escape")))
    transTable += "\n }"
    return transTable
  def getSearchCriteria(self, req):
    paramString = req.form[self.getQueryParam()]
    return InSearchCriteria(self.getModelProperty(), paramString and paramString.split(",") or [])


class TextFieldFilter(Filter):
  def getModelAndControllerJavascript(self, req, mapping):
    javascript = """
    function %(name)sModel (){}
    %(name)sModel.prototype = new BasicModel(["text"], "%(queryParam)s", "%(name)s");

    %(name)sModel.prototype.getSearchText = function() {
       return "%(itemText)s <b>" + this.text + "</b>";
    }

    %(objectModel)s = new %(name)sModel();


    function %(name)sController() {
       this.textControl = document.getElementById("%(name)sData");
    }

    %(name)sController.prototype = new FilterController("%(name)s", %(objectModel)s);
    
    %(name)sController.prototype.doOK = function() {
       document.searchController.addToSearch("%(name)s", {"text" : (this.textControl.value ? this.textControl.value : null)});
    }

    %(name)sController.prototype.clear = function() {
       this.textControl.value = ""
    }
    %(name)sController.prototype.populateControls = function () {
       if(this.model["text"])
          this.textControl.value = this.model["text"];
    }
    %(controllerName)s = new %(name)sController()
    """ % {"queryParam" : self.getQueryParam(), "name" : self.getName(), "objectModel" : self.getModelObjectName(),
           "controllerName" : self.getControllerName(),  "itemText" : self.getItemText()}
    return javascript;

  def getSearchCriteria(self, req):
    return BasicSearchCriteria(self.getModelProperty(), BasicSearchCriteria.OP_EQUAL, req.form[self.getQueryParam()])
          
  def getPopupContents(self, req):
    return """
            <div> <input id="%sData" type="text" name="%sDataName"> </input> </div> """ % (self.getName(), self.getName())

class SubstringMatchTextFilter(TextFieldFilter):
  def getSearchCriteria(self, req):
    return BasicSearchCriteria(self.getModelProperty(), BasicSearchCriteria.OP_LIKE, "%" + req.form[self.getQueryParam()] + "%")


class KeywordSearchFilter(TextFieldFilter):
  def getSearchCriteria(self, req):
    keywordList = req.form[self.getQueryParam()].split()
    resultCriteria = None
    for keyword in keywordList:
      curCriteria = BasicSearchCriteria(self.getModelProperty(), BasicSearchCriteria.OP_LIKE, '%' + keyword + '%')
      if not resultCriteria:
        resultCriteria = curCriteria
      else:
        resultCriteria = AndSearchCriteria(resultCriteria, curCriteria)
    return resultCriteria
  def getPopupContents(self, req):
    return """
            <div style="margin-bottom: 5px" > %s </div>
            <div> <input id="%sData" name="%sDataName"> </input> </div> """ % (self.getInstructionsText(), self.getName(), self.getName())
  def getInstructionsText():
    raise "Please override"

# This class is a hack because the *Criteria classes do %s replacement themselves rather than letting mysql do it.
class StringSelectBoxFilter(SelectBoxFilter):
  def getSearchCriteria(self, req):
    return BasicSearchCriteria(self.getModelProperty(), BasicSearchCriteria.OP_EQUAL, req.form[self.getQueryParam()])

