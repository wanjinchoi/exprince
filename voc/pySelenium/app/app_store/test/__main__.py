import sys
from voc.pySelenium.app.app_store.test.test_me import TU
from unittest import TestLoader, TextTestRunner

#############################################################
if __name__ == '__main__':
    suite = TestLoader().loadTestsFromTestCase(TU)
    result = TextTestRunner(verbosity=2).run(suite)
    sys.exit(ret)