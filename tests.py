import os
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
        self.db = UnQLite()
        self._filename = 'test.db'
        self.file_db = UnQLite(self._filename)

    def tearDown(self):
        if self.db.is_open:
            self.db.close()
        if self.file_db.is_open:
            self.file_db.close()
        if os.path.exists(self._filename):
            os.unlink(self._filename)

    def store_range(self, n, db=None):
        if db is None:
            db = self.db
        for i in range(n):
            db['k%s' % i] = str(i)


class TestKeyValueStorage(BaseTestCase):
    def test_basic_operations(self):
        for db in (self.db, self.file_db):
            db.store('k1', 'v1')
            db.store('k2', 'v2')
            self.assertEqual(db.fetch('k1'), b'v1')
            self.assertEqual(db.fetch('k2'), b'v2')
            self.assertRaises(KeyError, db.fetch, 'k3')

            db.delete('k2')
            self.assertRaises(KeyError, db.fetch, 'k2')

            self.assertTrue(db.exists('k1'))
            self.assertFalse(db.exists('k2'))

    def test_dict_interface(self):
        for db in (self.db, self.file_db):
            db['k1'] = 'v1'
            db['k2'] = 'v2'
            self.assertEqual(db['k1'], b'v1')
            self.assertEqual(db['k2'], b'v2')
            self.assertRaises(KeyError, lambda: db['k3'])

            del db['k2']
            self.assertRaises(KeyError, lambda: db['k2'])

            self.assertTrue('k1' in db)
            self.assertFalse('k2' in db)

    def test_append(self):
        self.db['k1'] = 'v1'
        self.db.append('k1', 'V1')
        self.assertEqual(self.db['k1'], b'v1V1')

        self.db.append('k2', 'V2')
        self.assertEqual(self.db['k2'], b'V2')

    def test_iteration(self):
        self.store_range(4, self.db)
        data = [item for item in self.db]
        self.assertEqual(data, [
            ('k0', b'0'),
            ('k1', b'1'),
            ('k2', b'2'),
            ('k3', b'3'),
        ])

        del self.db['k2']
        self.assertEqual([key for key, _ in self.db], ['k0', 'k1', 'k3'])

    def test_file_iteration(self):
        self.store_range(4, self.file_db)
        data = [item for item in self.file_db]
        self.assertEqual(data, [
            ('k3', b'3'),
            ('k2', b'2'),
            ('k1', b'1'),
            ('k0', b'0'),
        ])

        del self.file_db['k2']
        self.assertEqual([key for key, _ in self.file_db], ['k3', 'k1', 'k0'])

    def test_range(self):
        self.store_range(10, self.db)
        data = [item for item in self.db.range('k4', 'k6')]
        self.assertEqual(data, [
            ('k4', b'4'),
            ('k5', b'5'),
            ('k6', b'6'),
        ])

        data = [item for item in self.db.range('k8', 'kX')]
        self.assertEqual(data, [
            ('k8', b'8'),
            ('k9', b'9'),
        ])

        invalid_start = [item for item in self.db.range('kx', 'k2')]
        self.assertEqual(invalid_start, [])

    def test_file_range(self):
        self.store_range(10, self.file_db)
        data = [item for item in self.file_db.range('k6', 'k4')]
        self.assertEqual(data, [
            ('k6', b'6'),
            ('k5', b'5'),
            ('k4', b'4'),
        ])

        data = [item for item in self.file_db.range('k2', 'k0')]
        self.assertEqual(data, [
            ('k2', b'2'),
            ('k1', b'1'),
            ('k0', b'0'),
        ])

        invalid_start = [item for item in self.file_db.range('kx', 'k2')]
        self.assertEqual(invalid_start, [])

    def test_flush(self):
        for db in (self.db, self.file_db):
            self.store_range(10, db)
            self.assertEqual(len(list(db)), 10)
            db.flush()
            self.assertEqual(list(db), [])

    def test_len(self):
        for db in (self.db, self.file_db):
            self.store_range(10, db)
            self.assertEqual(len(db), 10)
            db.flush()
            self.assertEqual(len(db), 0)
            db['a'] = 'A'
            db['b'] = 'B'
            db['b'] = 'Bb'
            self.assertEqual(len(db), 2)

    def test_autocommit(self):
        self.file_db['k1'] = 'v1'
        self.file_db.close()
        self.file_db.open()
        self.assertEqual(self.file_db['k1'], b'v1')

        self.file_db.disable_autocommit()
        self.file_db['k2'] = 'v2'
        self.file_db.close()
        self.file_db.open()
        self.assertRaises(KeyError, lambda: self.file_db['k2'])

    def test_dict_methods(self):
        for db in (self.db, self.file_db):
            self.store_range(3, db)
            self.assertEqual(sorted(db.keys()), ['k0', 'k1', 'k2'])
            self.assertEqual(sorted(db.values()), [b'0', b'1', b'2'])
            self.assertEqual(sorted(db.items()), [
                ('k0', b'0'),
                ('k1', b'1'),
                ('k2', b'2')])

            db.update({'foo': 'bar', 'baz': 'nug'})
            self.assertEqual(db['foo'], b'bar')
            self.assertEqual(db['baz'], b'nug')

    def test_byte_strings(self):
        byte_data = [
            (b'k\xe4se', b'sp\xe4tzle'),
            (b'kn\xf6dli', b'br\xf6tli'),
            (b'w\xfcrstel', b's\xfclzli')]
        for db in (self.db, self.file_db):
            for k, v in byte_data:
                db.store(k, v)
            for k, v in byte_data:
                w = db.fetch(k)
                self.assertTrue(isinstance(w, bytes))
                self.assertEqual(w, v)


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
        self.assertEqual(self.file_db['k1'], b'v1')

        self.assertRaises(Exception , lambda: _test_failure('k2', 'v2'))
        self.assertRaises(KeyError, lambda: self.file_db['k2'])

    def test_context_manager(self):
        with self.file_db.transaction():
            self.file_db['foo'] = 'bar'

        self.assertEqual(self.file_db['foo'], b'bar')

        with self.file_db.transaction():
            self.file_db['baz'] = b'nug'
            self.file_db.rollback()

        self.assertRaises(KeyError, lambda: self.file_db['baz'])

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
        for db in (self.db, self.file_db):
            self.store_range(10, db)

    def assertIndex(self, cursor, idx):
        self.assertTrue(cursor.is_valid())
        self.assertEqual(cursor.key(), 'k%d' % idx)
        self.assertEqual(cursor.value(), str(idx).encode('utf-8'))

    def test_cursor_basic(self):
        cursor = self.db.cursor()
        self.assertIndex(cursor, 0)
        cursor.next_entry()
        self.assertIndex(cursor, 1)
        cursor.last()
        self.assertIndex(cursor, 9)
        cursor.previous_entry()
        self.assertIndex(cursor, 8)
        cursor.first()
        self.assertIndex(cursor, 0)
        cursor.delete()
        self.assertIndex(cursor, 1)
        del cursor

    def test_cursor_basic_file(self):
        cursor = self.file_db.cursor()
        cursor.first()
        self.assertIndex(cursor, 9)
        cursor.next_entry()
        self.assertIndex(cursor, 8)
        cursor.last()
        self.assertIndex(cursor, 0)
        cursor.previous_entry()
        self.assertIndex(cursor, 1)
        cursor.delete()
        self.assertIndex(cursor, 0)
        cursor.previous_entry()
        self.assertIndex(cursor, 2)
        cursor.next_entry()
        self.assertRaises(StopIteration, cursor.next_entry)

    def test_cursor_iteration(self):
        with self.db.cursor() as cursor:
            cursor.seek('k4')
            cursor.delete()
            cursor.reset()
            results = [item for item in cursor]
            self.assertEqual(results, [
                ('k0', b'0'),
                ('k1', b'1'),
                ('k2', b'2'),
                ('k3', b'3'),
                ('k5', b'5'),
                ('k6', b'6'),
                ('k7', b'7'),
                ('k8', b'8'),
                ('k9', b'9'),
            ])

            cursor.seek('k5')
            self.assertEqual(cursor.value(), b'5')
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
                    cursor.next_entry()
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


class TestJx9(BaseTestCase):
    def test_vm_reset(self):
        coll = self.db.collection('reg')
        self.assertTrue(coll.create())
        coll.store([{'key': i} for i in range(4)])

        vm = self.db.vm('$ret = db_fetch($collection);')
        vm.compile()
        vm['collection'] = 'reg'
        vm.execute()
        self.assertEqual(vm['ret'], {'__id': 0, 'key': 0})

        # Resetting and re-executing will return us the next record.
        vm.reset()
        vm.execute()
        self.assertEqual(vm['ret'], {'__id': 1, 'key': 1})

        vm.reset() ; vm.execute()
        self.assertEqual(vm['ret'], {'__id': 2, 'key': 2})
        vm.close()

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

        with self.db.vm(script) as vm:
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

        with self.db.vm(script) as vm:
            vm['values'] = values
            vm.execute()

            users = vm['users']
            self.assertEqual(users, [
                {'username': 'hubie', 'color': 'white', '__id': 0},
                {'username': 'michael', 'color': 'black', '__id': 1},
            ])


class TestCursorSilentError(BaseTestCase):
    def test_double_iteration_miscount(self):
        db = self.file_db
        val = 'x' * 100
        for i in range(500):
            db['k%07d' % i] = val

        self.assertEqual(
            len([k for k in db]),
            len([k for k in db]))

        db.close()
        db.open()

        # Raising "AssertionError: 500 != 490". What the fucking fuck.
        self.assertEqual(
            len([k for k in db]),
            len([k for k in db]))


class TestUtils(BaseTestCase):
    def test_random(self):
        ri = self.db.random_int()
        self.assertTrue(isinstance(ri, int))

        rs = self.db.random_string(10)
        self.assertEqual(len(rs), 10)


class TestCollection(BaseTestCase):
    def test_basic_crud_mem(self):
        self._test_basic_crud(self.db)

    def test_basic_crud_file(self):
        self._test_basic_crud(self.file_db)

    def _test_basic_crud(self, db):
        users = db.collection('users')
        self.assertFalse(users.creation_date())  # No creation date yet.
        self.assertTrue(users.create())
        self.assertFalse(users.create())  # Collection exists, not created.
        self.assertTrue(users.creation_date() != False)

        self.assertEqual(users.store({'username': 'huey'}), 0)
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 0,
            'username': 'huey'})

        self.assertEqual(users.store({'username': 'mickey'}), 1)
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 1,
            'username': 'mickey'})

        user_list = users.all()
        self.assertEqual(user_list, [
            {'__id': 0, 'username': 'huey'},
            {'__id': 1, 'username': 'mickey'},
        ])

        users.delete(1)
        self.assertEqual(users[0], {'__id': 0, 'username': 'huey'})
        self.assertTrue(users[1] is None)

        ret = users.update(0, {'color': 'white', 'name': 'hueybear'})
        self.assertTrue(ret)
        self.assertEqual(users[0], {
            '__id': 0,
            'color': 'white',
            'name': 'hueybear',
        })

        ret = users.update(1, {'name': 'zaizee'})
        self.assertFalse(ret)
        self.assertTrue(users[1] is None)

        self.assertEqual(users.all(), [
            {'__id': 0, 'color': 'white', 'name': 'hueybear'},
        ])

        ret = users.store({'name': 'new'})
        self.assertTrue(ret > 0)

        self.assertEqual(users[ret], {'name': 'new', '__id': ret})
        users[ret] = {'name': 'new-x', 'data': 123}
        self.assertEqual(users[ret], {'name': 'new-x', 'data': 123, '__id': ret})

    def test_basic_operations_mem(self):
        self._test_basic_operations(self.db)

    def test_basic_operations_file(self):
        self._test_basic_operations(self.file_db)

    def _test_basic_operations(self, db):
        users = db.collection('users')
        self.assertFalse(users.exists())
        self.assertTrue(users.create())
        self.assertTrue(users.exists())
        self.assertFalse(users.create())
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
            {'name': 'huey', 'activities': ['playing', 'sleeping'],
             '__id': 1}
        ])

        self.assertTrue(users[99] is None)

        # Drop collection and ensure does not exist.
        self.assertTrue(users.drop())
        self.assertFalse(users.exists())
        self.assertFalse(users.drop())

    def test_schema_mem(self):
        self._test_schema(self.db)

    def test_schema_file(self):
        self._test_schema(self.file_db)

    def _test_schema(self, db):
        # The schema does not appear to be enforced in any way by the library,
        # and is for metadata only.
        users = self.db.collection('users')

        # Non-existant collection or unset schema both return None.
        self.assertTrue(users.get_schema() is None)
        self.assertTrue(users.create())
        self.assertTrue(users.get_schema() is None)

        schema = {
            'username': 'string',
            'uid': 'integer',
            'admin': 'boolean'}
        self.assertTrue(users.set_schema(schema))
        self.assertEqual(users.get_schema(), schema)

        # Store a conforming and non-conforming record.
        u1 = users.store({'username': 'u1', 'uid': 1, 'admin': False})
        u2 = users.store({'username': 2, 'uid': '2', 'admin': None})
        self.assertEqual(users.all(), [
            {'__id': u1, 'username': 'u1', 'uid': 1, 'admin': False},
            {'__id': u2, 'username': 2, 'uid': '2', 'admin': None}])

    def test_fetch_current(self):
        users = self.db.collection('users')
        self.assertTrue(users.create())
        users.store({'username': 'u0'})
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 0,
            'username': 'u0'})

        users.store({'username': 'u1'})
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 1,
            'username': 'u1'})
        # Store does not overwrite, even if we specify an ID.
        users.store({'__id': 1, 'username': 'ux'})
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 2,
            'username': 'ux'})

        self.assertEqual(len(users), 3)

        # This should increment the cursor but since we are re-creating the VM
        # every time, it does not.
        self.assertEqual(users.current_record_id(), users.current_record_id())
        self.assertEqual(users.fetch_current(), {'__id': 0, 'username': 'u0'})

    def test_iter_collection(self):
        reg = self.db.collection('reg')
        self.assertTrue(reg.create())
        reg.store([{'k': j} for j in range(10)])

        # We can iterate over the collection.
        self.assertEqual([r['k'] for r in reg], list(range(10)))

        # We can also obtain a dedicated iterator and use it multiple times.
        it = reg.iterator()
        for x in range(10):
            self.assertEqual([r['k'] for r in it], list(range(10)))

    def test_independent_iterators(self):
        reg = self.db.collection('reg')
        self.assertTrue(reg.create())
        reg.store([{'k': j} for j in range(3)])

        i1 = iter(reg.iterator())
        self.assertEqual(next(i1), {'__id': 0, 'k': 0})
        self.assertEqual(next(i1), {'__id': 1, 'k': 1})
        i2 = iter(reg.iterator())
        self.assertEqual(next(i2), {'__id': 0, 'k': 0})
        self.assertEqual(next(i1), {'__id': 2, 'k': 2})
        self.assertRaises(StopIteration, lambda: next(i1))

    def test_unicode_key(self):
        users = self.db.collection('users')
        self.assertTrue(users.create())
        self.assertEqual(users.store({'key\u2020': 'value\u2019'}), 0)
        self.assertEqual(users.fetch(users.last_record_id()), {
            '__id': 0,
            'key\u2020': 'value\u2019',
        })

    def test_filtering(self):
        values = self.db.collection('values')
        self.assertTrue(values.create())
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

        filtered = values.filter(lambda obj: obj['val'] == 3 or obj['val'] == 5)
        self.assertEqual(filtered, [
            {'__id': 3, 'val': 3},
            {'__id': 5, 'val': 5}])

        kv = self.db.collection('kv')
        self.assertTrue(kv.create())
        for i in range(1, 10):
            kv.store({'k%d' % i: 'v%d' % i, 'data': i})

        filtered = kv.filter(lambda obj: obj.get('k1') == 'v1')
        self.assertEqual(filtered, [{'__id': 0, 'k1': 'v1', 'data': 1}])

        def filter_cb(obj):
            return obj['data'] % 3 == 0
        filtered = kv.filter(filter_cb)
        self.assertEqual(filtered, [
            {'__id': 2, 'k3': 'v3', 'data': 3},
            {'__id': 5, 'k6': 'v6', 'data': 6},
            {'__id': 8, 'k9': 'v9', 'data': 9}])

    def test_odd_values_mem(self):
        self._test_odd_values(self.db)

    def test_odd_values_file(self):
        self._test_odd_values(self.file_db)

    def _test_odd_values(self, db):
        coll = db.collection('testing')
        self.assertTrue(coll.create())
        coll.store({1: 2})
        res = coll.fetch(coll.last_record_id())
        self.assertEqual(res, [2, 0])

        self.assertTrue(coll.drop())

        # Try storing in non-existent collection?
        self.assertRaises(ValueError, lambda: coll.store({'f': 'f'}))

    def test_data_type_integrity(self):
        coll = self.db.collection('testing')
        self.assertTrue(coll.create())

        self.assertEqual(coll.store({
            'a': 'A',
            'b': 2,
            'c': 3.1,
            'd': True,
            'e': False,
            'f': 0,
            'g': u'\u2020',
            'h': [0, 1.5, True, None, u'\u2019', [1, 2], {'x': 'yz'}],
            'i': {'foo': 'bar', 'baz': 2},
        }), 0)

        res = coll.fetch(coll.last_record_id())
        self.assertEqual(res, {
            'a': 'A',
            'b': 2,
            'c': 3.1,
            'd': True,
            'e': False,
            'f': 0,
            'g': u'\u2020',
            'h': [0, 1.5, True, None, u'\u2019', [1, 2], {'x': 'yz'}],
            'i': {'foo': 'bar', 'baz': 2},
            '__id': 0})
        self.assertTrue(isinstance(res['d'], bool))
        self.assertTrue(isinstance(res['e'], bool))
        self.assertTrue(isinstance(res['f'], int))


if __name__ == '__main__':
    unittest.main(argv=sys.argv)
