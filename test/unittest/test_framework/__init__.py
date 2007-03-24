#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

import unittest
from test_core import suite as coreSuite
from test_util import suite as utilSuite
from test_formutils import suite as formutilsSuite
from test_properties import suite as propertiesSuite

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(coreSuite)
suite.addTest(utilSuite)
suite.addTest(formutilsSuite)
suite.addTest(propertiesSuite)

if __name__ == "__main__":
  runner = unittest.TextTestRunner()
  runner.run(suite)
