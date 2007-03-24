from model import AddressBookItem
from pywebmvc.framework.apache import Logger

class FileAddressBookHome:
  def __init__(self, filename):
    self.filename = filename
  def getLength(self):
    addressList = self.__readAllAddresses()
    return len(addressList)
  def find(self, searchCriteria, sortColumn, dir):
    addressList = self.__readAllAddresses()
    if sortColumn:
      addressList.sort(lambda x, y: cmp(getattr(x, sortColumn.property), getattr(y, sortColumn.property)))
    if dir == "desc":
      addressList.reverse()
    Logger.error("got here 22")
    if searchCriteria:
      Logger.error(repr(searchCriteria))
      Logger.error("len addresslist = " + str(len(addressList)))
      addressList = filter(lambda e: searchCriteria.accepts(e), addressList)
    return addressList
  def save(self, entry):
    if not entry.id:
      entry.id = self.__getNextId()
      fp = file(self.filename, "a")
      fp.write(self.__marshall(entry))
      fp.close()
    else:
      entryList = self.__readAllAddresses()
      entryList = filter(lambda e: e.id != entry.id, entryList)
      entryList.append(entry)
      entryList.sort(lambda x, y: cmp(x.id, y.id))
      data = "".join(map(lambda e: self.__marshall(e), entryList))
      fp = file(self.filename, "w")
      fp.write(data)
      fp.close()
  def findById(self, id):
    return filter(lambda x: x.id == id, self.__readAllAddresses())[0]
  def __readAllAddresses(self):
    try:
      fp = file(self.filename, "r")
      rawData = fp.read().strip()
      fp.close()
      lineData = rawData.split("\n")
    except IOError:
      lineData = []
    return map(lambda line: AddressBookItem(*line.split("##")), lineData)
  def __getNextId(self):
    addressList = self.__readAllAddresses()
    if not addressList:
      return 1
    return int(addressList[-1].id) + 1
  def __marshall(self, entry):
    return "##".join([str(entry.id), entry.firstName, entry.lastName, entry.street, entry.city, entry.state, entry.phone, entry.email]) + "\n"
  
