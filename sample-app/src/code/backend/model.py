from pywebmvc.framework.metadata import Entity

class AddressBookItem(Entity):
  def __init__(self, id=None, firstName=None, lastName=None, street=None, city=None, state=None, phone=None, email=None):
    self.id = id
    self.firstName=firstName
    self.lastName=lastName
    self.street=street
    self.city=city
    self.state=state
    self.phone=phone
    self.email=email
  def __repr__(self):
    return """ AddressBookItem(%s, %s, %s, %s, %s, %s, %s, %s) """ % (
      repr(self.id),
      repr(self.firstName),
      repr(self.lastName),
      repr(self.street),
      repr(self.city),
      repr(self.state),
      repr(self.phone),
      repr(self.email),
      )
    
    
