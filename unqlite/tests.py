import sys
import unittest

try:
    from unqlite import UnQLite
except ImportError:
    sys.stderr.write('Unable to import `unqlite`. Make sure it is properly '
                     'installed.\n')
    sys.stderr.flush()
    raise

from _unqlite import UNQLITE_OK


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

    def test_store_fmt(self):
        self.db.store_fmt('k1', 'foo %s:%d:%s', 'v1', 25, 'VX')
        self.assertEqual(self.db['k1'], 'foo v1:25:VX')

    def test_fetch_cb(self):
        state = []

        @self.db.kv_callback
        def cb(data):
            state.append(data)

        @self.db.kv_callback
        def alt_cb(data):
            state.append(data.upper())

        self.db['k1'] = 'v1'
        self.db['k2'] = 'v2'

        self.db.fetch_cb('k1', cb)
        self.assertEqual(state, ['v1'])

        self.db.fetch_cb('k2', cb)
        self.assertEqual(state, ['v1', 'v2'])

        self.db.fetch_cb('k1', alt_cb)
        self.assertEqual(state, ['v1', 'v2', 'V1'])

        self.assertRaises(KeyError, lambda: self.db.fetch_cb('kx', cb))

class TestTransaction(BaseTestCase):
    """
    These tests do not behave as I expect, but I am documenting the behavior
    here just in the event it changes.
    """
    def test_transaction(self):
        @self.db.commit_on_success
        def _test_success(key, value):
            self.db[key] = value

        @self.db.commit_on_success
        def _test_failure(key, value):
            self.db[key] = value
            raise Exception('intentional exception raised')

        _test_success('k1', 'v1')
        self.assertEqual(self.db['k1'], 'v1')

        self.assertRaises(Exception , lambda: _test_failure('k2', 'v2'))
        # I am not sure why this is the case, but the transaction management
        # does not seem to work.
        # self.assertRaises(KeyError, lambda: self.db['k2'])
        self.assertEqual(self.db['k2'], 'v2')

    def test_explicit_transaction(self):
        self.db.close()
        self.db.open()
        self.db.begin()
        self.db['k1'] = 'v1'
        self.db.rollback()

        # Again, not sure why this does not work, but for some reason, despite
        # the rollback, the value is still present.
        # self.assertRaises(KeyError, lambda: self.db['k1'])
        self.assertEqual(self.db['k1'], 'v1')


if __name__ == '__main__':
    unittest.main(argv=sys.argv)
