from pywebmvc.framework.core import HtmlPage, Action

class StubbedPage(HtmlPage):
  def getBodyStart(self,req,mapping):
    return super(StubbedPage,self).getBodyStart(req,mapping) + """
      <div>Stubbed out.</div>
    """

class StubbedAction(Action):
  def __call__(self,req,mapping):
    return mapping["success"]
