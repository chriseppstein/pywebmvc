#  START OF COPYRIGHT NOTICE
#  Copyright (c) 2004-2005. Teneros, Inc.
#  All Rights Reserved.
#  END OF COPYRIGHT NOTICE 

import unittest

loader = unittest.TestLoader()
suite = unittest.TestSuite()

if __name__ == "__main__":
  runner = unittest.TextTestRunner()
  runner.run(suite)
