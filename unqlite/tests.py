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
        self._filename = 'test.db'
        self.file_db = UnQLite(self._filename)

    def tearDown(self):
        try:
            self.file_db.close()
        except:
            pass
        if os.path.exists(self._filename):
            os.unlink(self._filename)

    def store_range(self, n, db=None):
        if db is None:
            db = self.db
        for i in range(n):
            db['k%s' % i] = str(i)


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
        self.store_range(4, self.db)
        data = [item for item in self.db]
        self.assertEqual(data, [
            ('k0', '0'),
            ('k1', '1'),
            ('k2', '2'),
            ('k3', '3'),
        ])

        del self.db['k2']
        self.assertEqual([key for key, _ in self.db], ['k0', 'k1', 'k3'])

    def test_file_iteration(self):
        self.store_range(4, self.file_db)
        data = [item for item in self.file_db]
        self.assertEqual(data, [
            ('k3', '3'),
            ('k2', '2'),
            ('k1', '1'),
            ('k0', '0'),
        ])

        del self.file_db['k2']
        self.assertEqual([key for key, _ in self.file_db], ['k3', 'k1', 'k0'])

    def test_range(self):
        self.store_range(10, self.db)
        data = [item for item in self.db.range('k4', 'k6')]
        self.assertEqual(data, [
            ('k4', '4'),
            ('k5', '5'),
            ('k6', '6'),
        ])

        data = [item for item in self.db.range('k8', 'kX')]
        self.assertEqual(data, [
            ('k8', '8'),
            ('k9', '9'),
        ])

        def invalid_start():
            data = [item for item in self.db.range('kx', 'k2')]
        self.assertRaises(Exception, invalid_start)

    def test_file_range(self):
        self.store_range(10, self.file_db)
        data = [item for item in self.file_db.range('k6', 'k4')]
        self.assertEqual(data, [
            ('k6', '6'),
            ('k5', '5'),
            ('k4', '4'),
        ])

        data = [item for item in self.file_db.range('k2', 'k0')]
        self.assertEqual(data, [
            ('k2', '2'),
            ('k1', '1'),
            ('k0', '0'),
        ])

        def invalid_start():
            data = [item for item in self.file_db.range('kx', 'k2')]
        self.assertRaises(Exception, invalid_start)

    def test_flush(self):
        self.store_range(10, self.db)
        self.assertEqual(len(list(self.db)), 10)
        self.db.flush()
        self.assertEqual(list(self.db), [])

    def test_file_flush(self):
        self.store_range(10, self.file_db)
        self.assertEqual(len(list(self.file_db)), 10)
        self.file_db.flush()
        self.assertEqual(list(self.file_db), [])

    def test_len(self):
        for db in [self.db, self.file_db]:
            self.store_range(10, db)
            self.assertEqual(len(db), 10)
            db.flush()
            self.assertEqual(len(db), 0)
            db['a'] = 'A'
            db['b'] = 'B'
            db['b'] = 'Bb'
            self.assertEqual(len(db), 2)


class TestTransaction(BaseTestCase):
    """
    We must use a file-based database to test the transaction functions. See
    http://unqlite.org/forum/trouble-with-transactions+1 for details.
    """
    def test_transaction(self):
        @self.file_db.commit_on_success
        def _test_success(key, value):
            self.file_db[key] = value

        @self.file_db.commit_on_success
        def _test_failure(key, value):
            self.file_db[key] = value
            raise Exception('intentional exception raised')

        _test_success('k1', 'v1')
        self.assertEqual(self.file_db['k1'], 'v1')

        self.assertRaises(Exception , lambda: _test_failure('k2', 'v2'))
        self.assertRaises(KeyError, lambda: self.file_db['k2'])

    def test_explicit_transaction(self):
        self.file_db.close()
        self.file_db.open()
        self.file_db.begin()
        self.file_db['k1'] = 'v1'
        self.file_db.rollback()

        self.assertRaises(KeyError, lambda: self.file_db['k1'])


class TestCursor(BaseTestCase):
    def setUp(self):
        super(TestCursor, self).setUp()
        for db in [self.db, self.file_db]:
            self.store_range(10, db)

    def assertIndex(self, cursor, idx):
        self.assertTrue(cursor.is_valid())
        self.assertEqual(cursor.key(), 'k%d' % idx)
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

    def test_cursor_basic_file(self):
        cursor = self.file_db.cursor()
        cursor.first()
        self.assertIndex(cursor, 9)
        cursor.next()
        self.assertIndex(cursor, 8)
        cursor.last()
        self.assertIndex(cursor, 0)
        cursor.previous()
        self.assertIndex(cursor, 1)
        cursor.delete()
        self.assertIndex(cursor, 0)
        cursor.previous()
        self.assertIndex(cursor, 2)
        cursor.next()
        self.assertRaises(StopIteration, cursor.next)

    def test_cursor_iteration(self):
        with self.db.cursor() as cursor:
            cursor.seek('k4')
            cursor.delete()
            cursor.reset()
            results = [item for item in cursor]
            self.assertEqual(results, [
                ('k0', '0'),
                ('k1', '1'),
                ('k2', '2'),
                ('k3', '3'),
                ('k5', '5'),
                ('k6', '6'),
                ('k7', '7'),
                ('k8', '8'),
                ('k9', '9'),
            ])

            cursor.seek('k5')
            self.assertEqual(cursor.value(), '5')
            keys = [key for key, _ in cursor]
            self.assertEqual(keys, ['k5', 'k6', 'k7', 'k8', 'k9'])

        with self.db.cursor() as cursor:
            self.assertRaises(Exception, cursor.seek, 'k4')
            cursor.seek('k5')
            keys = []
            while True:
                key = cursor.key()
                keys.append(key)
                if key == 'k7':
                    break
                else:
                    cursor.next()
        self.assertEqual(keys, ['k5', 'k6', 'k7'])

        # New items are appended to the end of the database.
        del self.db['k5']
        del self.db['k9']
        del self.db['k7']
        self.db['a0'] = 'x0'
        self.db['k5'] = 'x5'

        with self.db.cursor() as cursor:
            self.assertEqual(cursor.key(), 'k0')
            items = [k for k, _ in cursor]
            self.assertEqual(
                items,
                ['k0', 'k1', 'k2', 'k3', 'k6', 'k8', 'a0', 'k5'])

    def test_iterate_count(self):
        with self.db.cursor() as cursor:
            cursor_i = CursorIterator(cursor, 3)
            items = [item for item in cursor_i]
            self.assertEqual(items, [
                ('k0', '0'),
                ('k1', '1'),
                ('k2', '2'),
            ])

        with self.db.cursor() as cursor:
            cursor.next()
            items = [item for item in cursor.fetch_count(2)]
            self.assertEqual(items, [
                ('k1', '1'),
                ('k2', '2'),
            ])

        with self.db.cursor() as cursor:
            cursor.seek('k3')
            items = [item for item in cursor.fetch_until('k6')]
            self.assertEqual(items, [
                ('k3', '3'),
                ('k4', '4'),
                ('k5', '5'),
                ('k6', '6'),
            ])

            cursor.seek('k1')
            items = [item for item in cursor.fetch_until('k4', False)]
            self.assertEqual(items, [
                ('k1', '1'),
                ('k2', '2'),
                ('k3', '3'),
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

            self.assertEqual(keys, ['k9'])
            self.assertEqual(values, ['9'])

            cursor.previous()
            cursor.value_callback(vcb)

            self.assertEqual(keys, ['k9'])
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

    def test_foreign_function(self):
        script = "db_create('values'); db_store('values', $values);"
        values = [{'val': i} for i in range(20)]
        with self.db.compile_script(script) as vm:
            vm['values'] = values
            vm.execute()

        script = "$ret = db_fetch_all('values', my_filter_func);"
        with self.db.compile_script(script) as vm:
            @vm.foreign_function('my_filter_func')
            def _filter_func(context, obj):
                return obj['val'] in range(7, 13)

            vm.execute()
            result = vm['ret']

        self.assertEqual(result, [
            {'__id': 7, 'val': 7},
            {'__id': 8, 'val': 8},
            {'__id': 9, 'val': 9},
            {'__id': 10, 'val': 10},
            {'__id': 11, 'val': 11},
            {'__id': 12, 'val': 12},
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


class TestCollection(BaseTestCase):
    def test_basic_crud(self):
        users = self.db.collection('users')
        users.create()

        self.assertTrue(users.store({'username': 'huey'}))
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 0,
            'username': 'huey'})

        self.assertTrue(users.store({'username': u'mickey'}))
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 1,
            'username': u'mickey'})

        user_list = users.all()
        self.assertEqual(user_list, [
            {'__id': 0, 'username': 'huey'},
            {'__id': 1, 'username': 'mickey'},
        ])

        users.delete(1)
        self.assertEqual(users[0], {'__id': 0, 'username': 'huey'})
        self.assertIsNone(users[1])

        ret = users.update(0, {'color': 'white', 'name': 'hueybear'})
        self.assertTrue(ret)
        self.assertEqual(users[0], {
            '__id': 0,
            'color': 'white',
            'name': 'hueybear',
        })

        ret = users.update(1, {'name': 'zaizee'})
        self.assertFalse(ret)
        self.assertIsNone(users[1])

        self.assertEqual(users.all(), [
            {'__id': 0, 'color': 'white', 'name': 'hueybear'},
        ])

    def test_basic_operations(self):
        users = self.db.collection('users')
        self.assertFalse(users.exists())
        users.create()
        self.assertTrue(users.exists())
        self.assertEqual(len(users), 0)

        user_data = [
            {'name': 'charlie', 'activities': ['coding', 'reading']},
            {'name': 'huey', 'activities': ['playing', 'sleeping']},
            {'name': 'mickey', 'activities': ['sleeping', 'hunger']}]

        users.store(user_data)
        self.assertEqual(len(users), 3)

        users_with_ids = [record.copy() for record in user_data]
        for idx, record in enumerate(users_with_ids):
            record['__id'] = idx

        results = users.all()
        self.assertEqual(results, users_with_ids)

        users.store({'name': 'leslie', 'activities': ['reading', 'surgery']})
        self.assertEqual(len(users), 4)

        record = users.fetch_current()
        self.assertEqual(record['name'], 'charlie')

        self.assertEqual(users.fetch(3), {
            'name': 'leslie',
            'activities': ['reading', 'surgery'],
            '__id': 3})

        users.delete(0)
        users.delete(2)
        users.delete(3)
        self.assertEqual(users.all(), [
            {'name': 'huey', 'activities': ['playing', 'sleeping'], '__id': 1}
        ])

        self.assertIsNone(users[99])

    def test_unicode_key(self):
        users = self.db.collection('users')
        users.create()
        self.assertTrue(users.store({u'key': u'value'}))
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 0,
            'key': 'value',
        })

    def test_filtering(self):
        values = self.db.collection('values')
        values.create()
        value_data = [{'val': i} for i in range(20)]
        values.store(value_data)
        self.assertEqual(len(values), 20)

        filtered = values.filter(lambda obj: obj['val'] in range(7, 12))
        self.assertEqual(filtered, [
            {'__id': 7, 'val': 7},
            {'__id': 8, 'val': 8},
            {'__id': 9, 'val': 9},
            {'__id': 10, 'val': 10},
            {'__id': 11, 'val': 11},
        ])


if __name__ == '__main__':
    unittest.main(argv=sys.argv)
