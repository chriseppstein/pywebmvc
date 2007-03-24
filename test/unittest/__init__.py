#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

import unittest
from test_framework import suite as frameworkSuite
from test_tools import suite as toolsSuite

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTest(frameworkSuite)
suite.addTest(toolsSuite)

if __name__ == "__main__":
  runner = unittest.TextTestRunner()
  runner.run(suite)
