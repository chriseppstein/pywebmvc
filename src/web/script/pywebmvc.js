// Utility functions

function addParamToURL(url, paramName, value) {
   var searchString = "?" + paramName + "=" + value;
   
   var urlParts = url.split("?");
      
   if(urlParts.length > 1) {
      var tmpString = urlParts[1];
      if(tmpString) {
	 params = tmpString.split("&");
	 for(var i = 0; i < params.length; ++i) {
	    if(params[i].search(new RegExp("^" + paramName + "=")) == -1)
	       searchString += "&" + params[i];
	 }
      }
   }
    
   return urlParts[0] + searchString;
}

function appendParamsToURL(url, params) {
  var fullUrl = url;
  var first = url.indexOf("?") == -1;
  for (var i in params) {
     if(first) {
        fullUrl += "?";
        first = false;
     } else {
        fullUrl += "&";
     }
     fullUrl += i + "=" + encodeURIComponent(params[i]);
  }
  return fullUrl;
}

function removeParamsFromURL(url, attributeList) {
   if (url.indexOf("?") == -1)
      return url;

   var mainDivisions = url.split("?");
   var base = mainDivisions[0];
   var search = mainDivisions[1];
   var attrValues = search.split("&");

   var keptAttributes = new Object();

   for (var i = 0; i < attrValues.length; ++i) {
      var curAttrValueParts = attrValues[i].split("=");
      if(curAttrValueParts.length == 0 || isBlank(curAttrValueParts[0]) )
	 continue;
      var attribute = curAttrValueParts[0];
      var value = "";
      if (curAttrValueParts.length > 1)
	 value = curAttrValueParts[1];
      keptAttributes[attribute] = decodeURIComponent(value);
   }

   for (var i = 0; i < attributeList.length; ++i)
      delete keptAttributes[attributeList[i]];
   
   return appendParamsToURL(base, keptAttributes);
}

function getSelectValue(id) {
   var selectElem = document.getElementById(id);
   return selectElem.options[selectElem.selectedIndex].value;
}

function getSelectLabel(id) {
   var selectElem = document.getElementById(id);
   return selectElem.options[selectElem.selectedIndex].firstChild.nodeValue;
}

function getTextValue(id) {
   return document.getElementById(id).value;
}

function getRadioValue(idList) {
   for (var i = 0; i < idList.length; ++i) {
      var radioElem = document.getElementById(idList[i]);
      if (radioElem.checked)
	 return radioElem.value;
   }
   return "";
}

function getCheckValue(id) {
   var elem = document.getElementById(id);
   return elem.checked;
}

function extractValue(id) {
   if(typeof(id) == "object")
      return getRadioValue(id);

   var elem = document.getElementById(id);
   if(elem.type == "select-one")
      return getSelectValue(id);
   return elem.value;
}

function extractName(id) {
   var elem = typeof(id) == "string" ? document.getElementById(id) : document.getElementById(id[0]);
   return elem.name;
}

function setDisabledState(id, disabledState) {
   if(typeof(id) == "string") {
      document.getElementById(id).disabled = disabledState;
   } else {
      for (var i = 0; i < id.length; ++i) {
	 document.getElementById(id[i]).disabled = disabledState;
      }
   }
}

function getSelectedOptions(select) {
   var optionList = new Array();
   for(var i = 0; i < select.options.length; ++i) {
      if(select.options[i].selected)
	 optionList.push(select.options[i]);
   }
   return optionList;
}

function deleteSelectedOptions(select) {
   // can't delete more than one item from the list while traversing it in IE so do one at a time.
   var changeFound = true;
   while(changeFound) {
      changeFound = false;
      for(var i = 0; i < select.options.length; ++i) {
         if(select.options[i].selected) {
            select.options[i] = null;
            changeFound = true;
            break;
         }
      }
   }
}


function addOptions(select, optionsList) {
   for(var i = 0; i < optionsList.length; ++i) {
      select.options[select.options.length] = optionsList[i];
   }
}


function getXMLHttpRequestObject() {
   var req = false;
   // branch for native XMLHttpRequest object
   if(window.XMLHttpRequest) {
      try {
	 req = new XMLHttpRequest();
      } catch(e) {
	 req = false;
      }
      // branch for IE/Windows ActiveX version
   } else if(window.ActiveXObject) {
      try {
	 req = new ActiveXObject("Msxml2.XMLHTTP");
      } catch(e) {
	 try {
	    req = new ActiveXObject("Microsoft.XMLHTTP");
	 } catch(e) {
	    req = false;
	 }
      }
   }
   return req
}

function cloneObject(source) {
   var newObject = new Object();
   for (var i in source) {
       newObject[i] = source[i];
   }
   return newObject;
}

function isBlank(str) {
   return (!str || str.replace(/ /g, "") == "");
}

function zeroPad(numVal) {
   var s = String(numVal);
   if (s.length == 1)
      s = "0" + s;
   return s;
}

function jsDateToSQLLocal(date) {
   return makeSQLDateString(date.getFullYear(), date.getMonth() + 1, date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds());
}

function makeSQLDateString(year, month, day, hours, minutes, seconds) {
   return String(year) + "-" + zeroPad(month) + "-" + zeroPad(day) + " " + zeroPad(hours) + ":" + zeroPad(minutes) + ":" + zeroPad(seconds);
}

function setSelectTo(select, value) {
   for(var i = 0; i < select.options.length; ++i) {
      if(select.options[i].value == value)
	 select.selectedIndex = i;
   }
}

function cancelEvent(event)
{
  if (document.all)
  {
    event.cancelBubble = true;
    event.returnValue = false;
  }
  else
  {
    event.preventDefault();
    event.stopPropagation();
  }
  return false;
}

function confirmEvent(event, msg, obj)
{
  bResponse = confirm(msg);
  if (!bResponse)
  {
    cancelEvent(event);
    if (document.all)
    {
      if (typeof(obj) != "undefined"){
        obj.blur()
      }
    }
    return false;
  }
  return true;
}

function hasClassName(element, className)
{
  var classNames = element.className.split(" ");
  for (var i = 0; i < classNames.length; i++)
  {
    if (className == classNames[i])
    {
      return true;
    }
  }
  return false;
}


// Code that supports widget/form rendering

function returnKeyPressedInIEHandler(event)
{
  var RETURN_KEY = 13;
   
  if(document.all && event.keyCode == RETURN_KEY) {
     submitFirstFormButton();
     event.cancelBubble = true;
     event.keyCode = 0; // This is needed to prevent the IE beep
  }
}

function submitFirstFormButton() 
{
  // find first form button
  var formList = document.forms;
  
  for(formNum = 0; formNum < formList.length; ++formNum) {
     elementList = formList[formNum].elements;
     for(elementNum = 0; elementNum < elementList.length; ++elementNum) {
        curElement = elementList[elementNum];
        if(isButtonControlOrSubmitInput(curElement)) {
 	   curElement.click()
	   return
        }
     }
  }
}

function isButtonControlOrSubmitInput(element) {
   var submittable = !element.attributes.getNamedItem("dontSubmit")
   return (element.tagName.toLowerCase() == "button" && submittable) || (element.tagName.toLowerCase() == "input" && element.type.toLowerCase() == "submit");
}

function delRow(oButton,event)
{
  var oContainer = oButton.parentNode.parentNode;
  var containerType = oContainer.tagName.toLowerCase();
  if (containerType == "div") {
    oDiv = oContainer
    oParent = oDiv.parentNode;
    oParent.removeChild(oDiv);
    rebuttonDiv(oParent);
  } else if (containerType == "tr") {
    var oTableRow = oContainer;
    oParent = oTableRow.parentNode;
    oParent.removeChild(oTableRow);
    rebuttonTable(oParent);
  }

  return cancelEvent(event);
}

function addRow(oButton,event)
{
  var oContainer = oButton.parentNode.parentNode;
  var containerType = oContainer.tagName.toLowerCase();
  if (containerType == "div") {
    var oDiv = oContainer
    var oParent = oDiv.parentNode;
    var oInput = oDiv.getElementsByTagName("input")[0].cloneNode(true);
    oInput.value = "";
    var oNewDiv = document.createElement("div");
    oNewDiv.appendChild(oInput)
      oNewDiv.appendChild(document.createElement("span"));
    oParent.appendChild(oNewDiv)
      oInput.focus();
    rebuttonDiv(oParent);
  } else if (containerType == "tr") {
    var oTableRow = oContainer;
    var oNewRow = oTableRow.cloneNode(true);
    var inputs = oNewRow.getElementsByTagName("input")
    for (var i = 0; i < inputs.length; i++)
    {
      inputs[i].value = "";
    }
    var divs = oNewRow.getElementsByTagName("div")
    for (var i = 0; i < divs.length; i++)
    {
      divs[i].innerHTML = "";
    }
    oTableRow.parentNode.appendChild(oNewRow);
    rebuttonTable(oTableRow.parentNode);
  }
  return cancelEvent(event);
}

function rebuttonTable(oParent)
{
  lTrs = oParent.getElementsByTagName("TR");
  for (i = 0; i < lTrs.length; i++)
  {
    var bPlus = (i + 1 == lTrs.length);
    var bMinus = lTrs.length != 1;
    setTableButtons(lTrs[i], bPlus, bMinus);
  }
}

function rebuttonDiv(oParent)
{
  lDivs = oParent.getElementsByTagName("div");
  for (i = 0; i < lDivs.length; i++)
  {
    var bPlus = (i + 1 == lDivs.length);
    var bMinus = lDivs.length != 1;
    setDivButtons(lDivs[i], bPlus, bMinus);
  }
}

function setTableButtons(oTr, bPlus, bMinus)
{
  var oTd = document.createElement("td");
  var html = "";
  if (bMinus)
  {
    html += "<button type=\"button\" dontSubmit=\"true\" onclick=\"return delRow(this,event);\">-</button>";
  }
  if (bPlus)
  {
    html += "<button type=\"button\" dontSubmit=\"true\" onclick=\"return addRow(this,event);\">+</button>";
  }
  oTr.cells[oTr.cells.length -1].innerHTML = html;
}

function setDivButtons(oDiv, bPlus, bMinus)
{
  var oSpan = document.createElement("span");
  var html = ""
  if (bMinus)
  {
    html += "<button type=\"button\" dontSubmit=\"true\" onclick=\"return delRow(this,event);\">-</button>"
  }
  if (bPlus)
  {
    html += "<button type=\"button\" dontSubmit=\"true\" onclick=\"return addRow(this,event);\">+</button>"
  }
  oSpan.innerHTML = html;
  oDiv.replaceChild(oSpan, oDiv.getElementsByTagName("span")[0]);
}


// Used by the Pager Tool

function handleGotoPage(pageSize, listSize, pageParamName) {
    var pageInput = document.getElementById("gotoPageText");
    var itemNumber = parseInt(pageInput.value); 

    if (isNaN(itemNumber) || itemNumber < 1 || itemNumber > listSize) {
	alert("Bad Item Number: " + pageInput.value);
	return;
    }
	    
    var newPage = Math.floor((itemNumber - 1) / pageSize);
    location.href = addParamToURL(location.href, pageParamName, newPage);
}

function resetSubmitButtons()
{
  var buttons = document.getElementsByTagName("BUTTON");
  for (var i = 0; i < buttons.length; i++)
  {
    if (buttons[i].getAttribute("pwmvctype") == "submit")
    {
      buttons[i].nextSibling.disabled = true;
    }
  }
}
