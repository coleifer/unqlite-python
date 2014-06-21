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
    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.db = UnQLite(':mem:')


class TestKeyValueStorage(BaseTestCase):
    def test_basic_operations(self):
        self.db.store('k1', 'v1')
        self.db.store('k2', 'v2')
        self.assertEqual(self.db.fetch('k1'), 'v1')
        self.assertEqual(self.db.fetch('k2'), 'v2')
        self.assertRaises(KeyError, self.db.fetch, 'k3')

        self.db.delete('k2')
        self.assertRaises(KeyError, self.db.fetch, 'k2')

        self.assertTrue(self.db.exists('k1'))
        self.assertFalse(self.db.exists('k2'))

    def test_dict_interface(self):
        self.db['k1'] = 'v1'
        self.db['k2'] = 'v2'
        self.assertEqual(self.db['k1'], 'v1')
        self.assertEqual(self.db['k2'], 'v2')
        self.assertRaises(KeyError, lambda: self.db['k3'])

        del self.db['k2']
        self.assertRaises(KeyError, lambda: self.db['k2'])

        self.assertTrue('k1' in self.db)
        self.assertFalse('k2' in self.db)

    def test_append(self):
        self.db['k1'] = 'v1'
        self.db.append('k1', 'V1')
        self.assertEqual(self.db['k1'], 'v1V1')

        self.db.append('k2', 'V2')
        self.assertEqual(self.db['k2'], 'V2')

if __name__ == '__main__':
    unittest.main(argv=sys.argv)
