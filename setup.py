from distutils.core import setup
from os.path import exists

if exists("VERSION"):
  revFile = file("VERSION")
  ver = revFile.read()
  if ver[-1:] == '\n':
    ver = ver[:-1]
else:
  ver = "0.0.0"

setup(name='pywebmvc',
      version=ver,
      description='Python MVC Web Server Framework',
      author='Christopher Eppstein',
      author_email='chris.eppstein@teneros.com',
      url='http://www.teneros.com/opensource/pywebmvc/index.html',
      packages=[
                 'pywebmvc',
                 'pywebmvc.framework',
                 'pywebmvc.framework.render',
                 'pywebmvc.tools',
                 'pywebmvc.mock',
                 'pywebmvc.unittest',
                 'pywebmvc.unittest.test_framework',
                 'pywebmvc.unittest.test_tools',
               ],
      package_dir = {
                      'pywebmvc'      : 'src/code/pywebmvc',
                      'pywebmvc.mock' : 'test/mock',
                      'pywebmvc.unittest' : 'test/unittest',
                    },
      data_files = [
                     ('/opt/pywebmvc/style', ['src/web/style/pywebmvc.css',]),
                     ('/opt/pywebmvc/script', ['src/web/script/pywebmvc.js', 'src/web/script/searchtool.js', ]),
                     ('/opt/pywebmvc/resources/en', ['src/resources/en/ToolMessageResources.properties',]),
                   ],
     )
