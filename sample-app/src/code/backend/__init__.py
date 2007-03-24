import os, os.path
from FileBackedDB import FileAddressBookHome

backendInstance = None
def getBackend(request):
  global backendInstance
  if backendInstance is None:
    backendInstance = Backend(request)
  return backendInstance

class Backend:
  def __init__(self, request):
    self.addressBookHome = FileAddressBookHome(os.path.join(os.sep, "tmp", "pyWebMVCSampleAddressBook"))
  def getAddressBookHome(self):
    return self.addressBookHome


                                             
