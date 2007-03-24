function SearchController(itemName, modelList, resetParam) {
   this.modelList = modelList;
   this.modelHash = {}
   for (var i = 0; i < modelList.length; ++i) {
      this.modelHash[modelList[i].getName()] = modelList[i];
   }

   this.urlConstructor = new URLConstructor(modelList);
   this.searchTextCreator = new SearchTextCreator(itemName, modelList);
   this.resetButton = document.getElementById("searchResetButton");
   this.resetParam = resetParam;
}

SearchController.prototype.addToSearch = function(name, newData) {
   this.modelHash[name].update(newData);
   this.updateControls();
   this.handleSubmit(false);
}

SearchController.prototype.displayInitialValues = function() {
   this.updateControls();
   this.staticSearch = document.getElementById("staticSearch");
   if(this.staticSearch) {
      this.staticSearch.innerHTML = this.searchTextCreator.makeText();
   }
}

SearchController.prototype.updateControls = function () {
   if (gAreModelsEmpty(this.modelList)) {
      this.resetButton.disabled=true;
   } else {
      this.resetButton.disabled=false;
   }
}

SearchController.prototype.handleSubmit = function(isReset) {
   var url = this.urlConstructor.makeURL();
   if(isReset)
      url = addParamToURL(url, this.resetParam, "true");
   location.href = url;
}

SearchController.prototype.handleReset = function() {
   for(var i = 0; i < this.modelList.length; ++i) {
      this.modelList[i].clear();
   }
   this.updateControls();	
   this.handleSubmit(true);
}


function gAreModelsEmpty(modelList) {
   for(var i = 0; i < modelList.length; ++i) {
      if(!modelList[i].isEmpty())
	 return false;
   }
   return true;
}


function Model(name) {
   this.modelName = name;
}

Model.prototype.getName = function(){
   return this.modelName;
}

Model.prototype.update = function(data) {
   alert("override");
}

Model.prototype.isEmpty = function() {
   alert("override");
}

Model.prototype.clear = function() {
   alert("override");
}

Model.prototype.getSearchText = function() {
   alert("override");
}

Model.prototype.getURLAttributeName = function() {
   alert("override");
}

Model.prototype.getURLValue = function() {
   alert("override");
}

Model.prototype.initializeFromURLValue = function(urlValue) {
   alert("override")
}

// This class represents a model that defines most of the basic operations on a model
// In the best case scenario you would only need to override getSearchText
function BasicModel(attrList, queryParam, name) {
   this.queryParam = queryParam;
   this.attrList = attrList;
   this.name = name;
}

BasicModel.prototype = new Model("");

BasicModel.prototype.getName = function() {
   return this.name;
}

BasicModel.prototype.update = function(data) {
   for (attr in data) {
      this[attr] = data[attr];
   }
}

BasicModel.prototype.isEmpty = function() {
   for(var i = 0; i < this.attrList.length; ++i) {
      if (this[this.attrList[i]] != null) 
         return false;
   }
   return true;
}

BasicModel.prototype.clear = function() {
   for(var i = 0; i < this.attrList.length; ++i) {
      this[this.attrList[i]] = null;
   }
}

BasicModel.prototype.getURLAttributeName = function() {
   return this.queryParam;
}

BasicModel.prototype.getURLValue = function() {
   var result = ""
   for(var i = 0; i < this.attrList.length; ++i) {
      if (i != 0) result += ",";
      result += this[this.attrList[i]]
   }
   return result;
}

BasicModel.prototype.initializeFromURLValue = function(urlValue) {
   var values = urlValue.split(",");
   for(var i = 0; i < this.attrList.length; ++i)
      this[this.attrList[i]] = values[i];
}

function SearchTextCreator(itemName, modelList) {
   this.modelList = modelList;
   this.itemName = itemName;
}

SearchTextCreator.prototype.makeText = function() {
   if(gAreModelsEmpty(this.modelList))
      return document.getElementById("searchDefaultText").innerHTML;
   var text = this.itemName + " ";
   for(var i = 0; i < this.modelList.length; ++i) {
      if (!this.modelList[i].isEmpty())
	 text += this.modelList[i].getSearchText() + " ";
   }
   return text;
}


function URLConstructor(modelList) {
   this.modelList = modelList;
}

URLConstructor.prototype.makeURL = function() {
    var allAttributes = new Array();
    var selectedAttributes = new Object();

    for (var i = 0; i < this.modelList.length; ++i) {
       var curModel = this.modelList[i];
       allAttributes.push(curModel.getURLAttributeName());
	  
       if(!curModel.isEmpty()) {
	   selectedAttributes[curModel.getURLAttributeName()] = curModel.getURLValue();
       }
    }

    var url = removeParamsFromURL(location.href, allAttributes);
    return appendParamsToURL(url, selectedAttributes);
}

function FilterController(name, model) {
   this.name = name;
   this.model = model;
   this.popupForm = document.getElementById(name + "PopupForm");
   this.handleInternalClick = function (event) {
      if(!document.all) {
	 event.stopPropagation();
      }        
      else {
	 window.event.cancelBubble = true;
      }
   }
}

FilterController.prototype.handleMainButton = function() {
   if (this.isPopupVisible())
      this.handleCancel();
   else
      this.showPopup();
}

FilterController.prototype.handleOK = function() {
   this.doOK();
   this.hidePopup();
}

FilterController.prototype.handleCancel = function() {
   this.clear();
   this.hidePopup();
}

FilterController.prototype.isPopupVisible = function() {
   return this.popupForm.style.display != "none"
}

FilterController.prototype.showPopup = function() {
   this.populateControls();
   this.popupForm.style.display = "block";
   this.addHandlers()
}

FilterController.prototype.hidePopup = function() {
   this.popupForm.style.display = "none"
}

FilterController.prototype.doOK = function() {
   alert("doOK needs to be overridden");
}

FilterController.prototype.clear = function() {
   alert("clear needs to be overridden");
}

FilterController.prototype.populateControls = function() {
   alert("populateControls needs to be overridden");
}

// add handlers to stop event propagation within popup, and a handler to cause the popup to go away on an external click
FilterController.prototype.addHandlers = function() {
   var self = this;
   var cnt = 0;
   var bodyElem = document.body

   this.removeHandlers()

   this.handleExternalClick = function(event) {
      if (cnt == 1)
         self.hidePopup();
      cnt += 1;
   }

    if(!document.all) {
	bodyElem.addEventListener("click", this.handleExternalClick, false);
        this.popupForm.addEventListener("click", this.handleInternalClick, false);
    } else {
        bodyElem.attachEvent("onclick", this.handleExternalClick);
        this.popupForm.attachEvent("onclick", this.handleInternalClick);
    }
}

FilterController.prototype.removeHandlers = function () {
   var bodyElem = document.body;

   if(this.handleExternalClick) {
      if(!document.all) {
	 bodyElem.removeEventListener("click", this.handleExternalClick, false);
	 this.popupForm.removeEventListener("click", this.handleInternalClick, false);
      } else {
	 bodyElem.detachEvent("onclick", this.handleExternalClick);
	 this.popupForm.detachEvent("click", this.handleInternalClick);
      }
   }
}

