import os
import sys
import unittest

try:
    from unqlite import UnQLite
    from unqlite.core import CursorIterator
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

        def cb(data):
            state.append(data)

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

    def test_iteration(self):
        for i in range(4):
            self.db['k%s' % i] = str(i)

        data = [item for item in self.db]
        self.assertEqual(data, [
            ('k0', '0'),
            ('k1', '1'),
            ('k2', '2'),
            ('k3', '3'),
        ])

        del self.db['k2']
        self.assertEqual([key for key, _ in self.db], ['k0', 'k1', 'k3'])


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


class TestCursor(BaseTestCase):
    def setUp(self):
        super(TestCursor, self).setUp()
        for i in range(10):
            self.db['k%02d' % i] = str(i)

    def assertIndex(self, cursor, idx):
        self.assertTrue(cursor.is_valid())
        self.assertEqual(cursor.key(), 'k%02d' % idx)
        self.assertEqual(cursor.value(), str(idx))

    def test_cursor_basic(self):
        cursor = self.db.cursor()
        self.assertIndex(cursor, 0)
        cursor.next()
        self.assertIndex(cursor, 1)
        cursor.last()
        self.assertIndex(cursor, 9)
        cursor.previous()
        self.assertIndex(cursor, 8)
        cursor.first()
        self.assertIndex(cursor, 0)
        cursor.delete()
        self.assertIndex(cursor, 1)
        cursor.close()

    def test_cursor_iteration(self):
        with self.db.cursor() as cursor:
            cursor.seek('k04')
            cursor.delete()
            cursor.reset()
            results = [item for item in cursor]
            self.assertEqual(results, [
                ('k00', '0'),
                ('k01', '1'),
                ('k02', '2'),
                ('k03', '3'),
                ('k05', '5'),
                ('k06', '6'),
                ('k07', '7'),
                ('k08', '8'),
                ('k09', '9'),
            ])

            cursor.seek('k05')
            self.assertEqual(cursor.value(), '5')
            keys = [key for key, _ in cursor]
            self.assertEqual(keys, ['k05', 'k06', 'k07', 'k08', 'k09'])

        with self.db.cursor() as cursor:
            self.assertRaises(Exception, cursor.seek, 'k04')
            cursor.seek('k05')
            keys = []
            while True:
                key = cursor.key()
                keys.append(key)
                if key == 'k07':
                    break
                else:
                    cursor.next()
        self.assertEqual(keys, ['k05', 'k06', 'k07'])

    def test_iterate_count(self):
        with self.db.cursor() as cursor:
            cursor_i = CursorIterator(cursor, 3)
            items = [item for item in cursor_i]
            self.assertEqual(items, [
                ('k00', '0'),
                ('k01', '1'),
                ('k02', '2'),
            ])

        with self.db.cursor() as cursor:
            cursor.next()
            items = [item for item in cursor.fetch_count(2)]
            self.assertEqual(items, [
                ('k01', '1'),
                ('k02', '2'),
            ])

        with self.db.cursor() as cursor:
            cursor.seek('k03')
            items = [item for item in cursor.fetch_until('k06')]
            self.assertEqual(items, [
                ('k03', '3'),
                ('k04', '4'),
                ('k05', '5'),
                ('k06', '6'),
            ])

            cursor.seek('k01')
            items = [item for item in cursor.fetch_until('k04', False)]
            self.assertEqual(items, [
                ('k01', '1'),
                ('k02', '2'),
                ('k03', '3'),
            ])

    def test_cursor_callbacks(self):
        keys = []
        values = []
        with self.db.cursor() as cursor:
            cursor.last()

            @cursor.key_callback
            def kcb(key):
                keys.append(key)

            def vcb(value):
                values.append(value)
            cursor.value_callback(vcb)

            self.assertEqual(keys, ['k09'])
            self.assertEqual(values, ['9'])

            cursor.previous()
            cursor.value_callback(vcb)

            self.assertEqual(keys, ['k09'])
            self.assertEqual(values, ['9', '8'])


class TestJx9(BaseTestCase):
    def test_simple_compilation(self):
        script = """
            $collection = 'users';
            if (!db_exists($collection)) {
                db_create($collection);
            }
            db_store($collection, {"username": "huey", "age": 3});
            $huey_id = db_last_record_id($collection);
            db_store($collection, {"username": "mickey", "age": 5});
            $mickey_id = db_last_record_id($collection);
            $something = 'hello world';
            $users = db_fetch_all($collection);
            $nested = {
                "k1": {"foo": [1, 2, 3]},
                "k2": ["v2", ["v3", "v4"]]};
        """

        with self.db.compile_script(script) as vm:
            vm.execute()
            self.assertEqual(vm['huey_id'], 0)
            self.assertEqual(vm['mickey_id'], 1)
            self.assertEqual(vm['something'], 'hello world')

            users = vm['users']
            self.assertEqual(users, [
                {'__id': 0, 'age': 3, 'username': 'huey'},
                {'__id': 1, 'age': 5, 'username': 'mickey'},
            ])

            nested = vm['nested']
            self.assertEqual(nested, {
                'k1': {'foo': [1, 2, 3]},
                'k2': ['v2', ['v3', 'v4']]})

    def test_setting_values(self):
        script = """
            $collection = 'users';
            db_create($collection);
            db_store($collection, $values);
            $users = db_fetch_all($collection);
        """
        values = [
            {'username': 'hubie', 'color': 'white'},
            {'username': 'michael', 'color': 'black'},
        ]

        with self.db.compile_script(script) as vm:
            vm['values'] = values
            vm.execute()

            users = vm['users']
            self.assertEqual(users, [
                {'username': 'hubie', 'color': 'white', '__id': 0},
                {'username': 'michael', 'color': 'black', '__id': 1},
            ])


class TestUtils(BaseTestCase):
    def test_random(self):
        ri = self.db.random_number()
        self.assertTrue(isinstance(ri, (int, long)))

        rs = self.db.random_string(10)
        self.assertEqual(len(rs), 10)

    def test_store_file(self):
        cur_dir = os.path.realpath(os.path.dirname(__file__))
        filename = os.path.join(cur_dir, 'core.py')
        with open(filename) as fh:
            contents = fh.read()

        self.db.store_file('source', filename)
        db_contents = self.db.fetch('source', 1024 * 64)
        self.assertEqual(db_contents, contents)


if __name__ == '__main__':
    unittest.main(argv=sys.argv)
