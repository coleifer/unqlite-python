import sys
import unittest

try:
    from unqlite import UnQLite
except ImportError:
    sys.stderr.write('Unable to import `unqlite`. Make sure it is properly '
                     'installed.\n')
    sys.stderr.flush()
    raise


class BaseTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main(argv=sys.argv)
