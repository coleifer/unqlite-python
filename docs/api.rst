.. _api:

API Documentation
=================

.. py:class:: UnQLite([filename=':mem:'[, flags=UNQLITE_OPEN_CREATE[, open_database=True]])

    The :py:class:`UnQLite` object provides a pythonic interface for interacting
    with `UnQLite databases <http://unqlite.symisc.net/>`_. UnQLite is a lightweight,
    embedded NoSQL database and JSON document store.

    :param str filename: The path to the database file.
    :param int flags: How the database file should be opened.
    :param bool open_database: When set to ``True``, the database will be opened automatically when the class is instantiated. If set to ``False`` you will need to manually call :py:meth:`~UnQLite.open`.

    .. note::
        UnQLite supports in-memory databases, which can be created by passing in ``':mem:'`` as the database file. This is the default behavior if no database file is specified.

    Example usage:

    .. code-block:: pycon

        >>> db = UnQLite()  # Create an in-memory database.
        >>> db['foo'] = 'bar'  # Use as a key/value store.
        >>> print db['foo']
        bar

        >>> for i in range(4):
        ...     db['k%s' % i] = str(i)
        ...

        >>> 'k3' in db
        True
        >>> 'k4' in db
        False
        >>> del db['k3']

        >>> db.append('k2', 'XXXX')
        >>> db['k2']
        '2XXXX'

        >>> with db.cursor() as cursor:
        ...     for key, value in cursor:
        ...         print key, '=>', value
        ...
        foo => bar
        k0 => 0
        k1 => 1
        k2 => 2XXXX

        >>> script = """
        ...     db_create('users');
        ...     db_store('users', $list_of_users);
        ...     $users_from_db = db_fetch_all('users');
        ... """

        >>> list_of_users = [
        ...     {'username': 'Huey', 'age': 3},
        ...     {'username': 'Mickey', 'age': 5}
        ... ]

        >>> with db.vm(script) as vm:
        ...     vm['list_of_users'] = list_of_users
        ...     vm.execute()
        ...     users_from_db = vm['users_from_db']
        ...
        True

        >>> users_from_db  # UnQLite assigns items in a collection an ID.
        [{'username': 'Huey', 'age': 3, '__id': 0},
         {'username': 'Mickey', 'age': 5, '__id': 1}]

    .. py:method:: open()

        Open the database. This method should only be called if the database was manually closed, or if the database was instantiated with ``open_database=False``.

        Valid flags:

        * ``UNQLITE_OPEN_CREATE``
        * ``UNQLITE_OPEN_READONLY``
        * ``UNQLITE_OPEN_READWRITE``
        * ``UNQLITE_OPEN_CREATE``
        * ``UNQLITE_OPEN_EXCLUSIVE``
        * ``UNQLITE_OPEN_TEMP_DB``
        * ``UNQLITE_OPEN_NOMUTEX``
        * ``UNQLITE_OPEN_OMIT_JOURNALING``
        * ``UNQLITE_OPEN_IN_MEMORY``
        * ``UNQLITE_OPEN_MMAP``

        Detailed descriptions of these flags can be found in the `unqlite_open docs <http://unqlite.org/c_api/unqlite_open.html>`_.

    .. py:method:: close()

        Close the database.

        .. warning::
            If you are using a file-based database, by default any uncommitted changes will be committed when the database is closed. If you wish to discard uncommitted changes, you can use :py:meth:`~UnQLite.disable_autocommit`.

    .. py:method:: __enter__()

        Use the database as a context manager, opening the connection and closing it at the end of the wrapped block:

        .. code-block:: python

            with UnQLite('my_db.udb') as db:
                db['foo'] = 'bar'

            # When the context manager exits, the database is closed.

    .. py:method:: disable_autocommit()

        When the database is closed, prevent any uncommitted writes from being saved.

        .. note:: This method only affects file-based databases.

    .. py:method:: store(key, value)

        Store a value in the given key.

        :param str key: Identifier used for storing data.
        :param str value: A value to store in UnQLite.

        Example:

        .. code-block:: python

            db = UnQLite()
            db.store('some key', 'some value')
            db.store('another key', 'another value')

        You can also use the dictionary-style ``db[key] = value`` to store a value:

        .. code-block:: python

            db['some key'] = 'some value'

    .. py:method:: fetch(key)

        Retrieve the value stored at the given ``key``. If no value exists in the given key, a ``KeyError`` will be raised.

        :param str key: Identifier to retrieve
        :returns: The data stored at the given key
        :raises: ``KeyError`` if the given key does not exist.

        Example:

        .. code-block:: python

            db = UnQLite()
            db.store('some key', 'some value')
            value = db.fetch('some key')

        You can also use the dictionary-style ``value = db[key]`` lookup to retrieve a value:

        .. code-block:: python

            value = db['some key']

    .. py:method:: delete(key)

        Remove the key and its associated value from the database.

        :param str key: The key to remove from the database.
        :raises: ``KeyError`` if the given key does not exist.

        Example:

        .. code-block:: python

            def clear_cache():
                db.delete('cached-data')

        You can also use the python ``del`` keyword combined with a dictionary lookup:

        .. code-block:: python

            def clear_cache():
                del db['cached-data']

    .. py:method:: append(key, value)

        Append the given ``value`` to the data stored in the ``key``. If no data exists, the operation is equivalent to :py:meth:`~UnQLite.store`.

        :param str key: The identifier of the value to append to.
        :param value: The value to append.

    .. py:method:: exists(key)

        Return whether the given ``key`` exists in the database.

        :param str key:
        :returns: A boolean value indicating whether the given ``key`` exists in the database.

        Example:

        .. code-block:: python

            def get_expensive_data():
                if not db.exists('cached-data'):
                    db.set('cached-data', calculate_expensive_data())
                return db.get('cached-data')

        You can also use the python ``in`` keyword to determine whether a key exists:

        .. code-block:: python

            def get_expensive_data():
                if 'cached-data' not in db:
                    db['cached-data'] = calculate_expensive_data()
                return db['cached-data']

    .. py:method:: begin()

        Begin a transaction.

    .. py:method:: rollback()

        Roll back the current transaction.

    .. py:method:: commit()

        Commit the current transaction.

    .. py:method:: transaction()

        Create a context manager for performing multiple operations in a transaction.

        .. warning::
            Transactions occur at the disk-level and have no effect on in-memory databases.

        Example:

        .. code-block:: python

            # Transfer $100 in a transaction.
            with db.transaction():
                db['from_acct'] = db['from_account'] - 100
                db['to_acct'] = db['to_acct'] + 100

            # Make changes and then roll them back.
            with db.transaction():
                db['foo'] = 'bar'
                db.rollback()  # Whoops, do not commit these changes.

    .. py:method:: commit_on_success(fn)

        Function decorator that will cause the wrapped function to have all statements wrapped in a transaction. If the function returns without an exception, the transaction is committed. If an exception occurs in the function, the transaction is rolled back.

        Example:

        .. code-block:: pycon

            >>> @db.commit_on_success
            ... def save_value(key, value, exc=False):
            ...     db[key] = value
            ...     if exc:
            ...         raise Exception('uh-oh')
            ...
            >>> save_value('k3', 'v3')
            >>> save_value('k3', 'vx', True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in <module>
              File "unqlite/core.py", line 312, in wrapper
                return fn()
              File "<stdin>", line 5, in save_value
            Exception: uh-oh
            >>> db['k3']
            'v3'

    .. py:method:: cursor()

        :returns: a :py:class:`Cursor` instance.

        Create a cursor for traversing database records.

    .. py:method:: vm(code)

        :param str code: a Jx9 script.
        :returns: a :py:class:`VM` instance with the compiled script.

        Compile the given Jx9 script and return an initialized :py:class:`VM` instance.

        Usage:

        .. code-block:: python

            script = "$users = db_fetch_all('users');"
            with db.vm(script) as vm:
                vm.execute()
                users = vm['users']

    .. py:method:: collection(name)

        :param str name: The name of the collection.

        Factory method for instantiating a :py:class:`Collection` for working with a collection of JSON objects.

        Usage:

        .. code-block:: python

            Users = db.collection('users')

            # Fetch all records in the collection.
            all_users = Users.all()

            # Create a new record.
            Users.store({'name': 'Charlie', 'activities': ['reading', 'programming']})

        See the :py:class:`Collection` docs for more examples.

    .. py:method:: keys()

        :returns: A generator that successively yields the keys in the database.

    .. py:method:: values()

        :returns: A generator that successively yields the values in the database.

    .. py:method:: items()

        :returns: A generator that successively yields tuples containing the keys and values in the database.

    .. py:method:: update(data)

        :param dict data: Dictionary of data to store in the database. If any keys in ``data`` already exist, the values will be overwritten.

    .. py:method:: __iter__()

        UnQLite databases can be iterated over. The iterator is a :py:class:`Cursor`, and will yield 2-tuples of keys and values:

        .. code-block:: python

            db = UnQLite('my_db.udb')
            for (key, value) in db:
                print key, '=>', value

    .. py:method:: range(start_key, end_key[, include_end_key=True])

        Iterate over a range of key/value pairs in the database.

        .. code-block:: python

            for key, value in db.range('d.20140101', 'd.20140201', False):
                calculate_daily_aggregate(key, value)

    .. py:method:: __len__()

        Return the number of records in the database.

        .. warning:: This method calculates the lengthy by iterating and counting every record. At the time of writing, there is no C API for calculating the size of the database.

    .. py:method:: flush()

        Delete all records in the database.

        .. warning:: This method works by iterating through all the records and deleting them one-by-one. At the time of writing there is no API for bulk deletes. If you are worried about speed, simply delete the database file and re-open it.

    .. py:method:: random_string(nbytes)

        :param int nbytes: number of bytes to generate
        :returns: a string consisting of random lower-case letters (a-z).

    .. py:method:: random_number()

        :returns: a random positive integer

    .. py:method:: lib_version()

        :returns: The UnQLite library version.


.. py:class:: Transaction(unqlite)

    :param UnQLite unqlite: An :py:class:`UnQLite` instance.

    Context-manager for executing wrapped blocks in a transaction. Rather than instantiating this object directly, it is recommended that you use :py:meth:`UnQLite.transaction`.

    Example:

    .. code-block:: python

        with db.transaction():
            db['from_acct'] = db['from_acct'] + 100
            db['to_acct'] = db['to_acct'] - 100

    To roll back changes inside a transaction, call :py:meth:`UnQLite.rollback`:

    .. code-block:: python

        with db.transaction():
            db['from_acct'] = db['from_acct'] + 100
            db['to_acct'] = db['to_acct'] - 100
            if int(db['to_acct']) < 0:
                db.rollback()  # Not enough funds!


.. py:class:: Cursor(unqlite)

    :param UnQLite unqlite: An :py:class:`UnQLite` instance.

    Create a cursor. Cursors should generally be used as context managers.

    Rather than instantiating this class directly, it is preferable to call the factory method :py:meth:`UnQLite.cursor`.

    .. code-block:: python

        for i in range(4):
            db['k%d' % i] = str(i)

        # Cursor support iteration, which returns key/value pairs.
        with db.cursor() as cursor:
            all_items = [(key, value) for key, value in cursor]

            # You can seek to a record, then iterate to retrieve a portion
            # of results.
            cursor.seek('k2')
            k2, k3 = [key for key, _ in cursor]

        # Previous cursor was closed automatically, open a new one.
        with db.cursor() as cursor:
            cursor.seek('k1')  # Jump to the 2nd record, k1
            assert cursor.key() == 'k1'  # Use the key()/value() methods.
            assert cursor.value() == '1'

            cursor.delete()  # Delete k1/v1
            cursor.first()  # Cursor now points to k0/0
            cursor.next()  # Cursor jumps to k2/2 since k1/1 is deleted.
            assert cursor.key() == 'k2'

            keys = [key for key, value in cursor]  # Cursor iterates from k2->k3
            assert keys == ['k2', 'k3']

    .. py:method:: reset()

        Reset the cursor, which also resets the pointer to the first record.

    .. py:method:: seek(key[, flags=UNQLITE_CURSOR_MATCH_EXACT])

        Advance the cursor to the given key using the comparison method
        described in the flags.

        A detailed description of alternate flags and their usage can be found in the `unqlite_kv_cursor docs <http://unqlite.org/c_api/unqlite_kv_cursor.html>`_.

        Usage:

        .. code-block:: python

            with db.cursor() as cursor:
                cursor.seek('item.20140101')
                while cursor.is_valid():
                    data_for_day = cursor.value()
                    # do something with data for day
                    handle_data(data_for_day)
                    if cursor.key() == 'item.20140201':
                        break
                    else:
                        cursor.next()

    .. py:method:: first()

        Place cursor at the first record.

    .. py:method:: last()

        Place cursor at the last record.

    .. py:method:: next_entry()

        Move the cursor to the next record.

        :raises: ``StopIteration`` if you have gone past the last record.

    .. py:method:: previous_entry()

        Move the cursor to the previous record.

        :raises: ``StopIteration`` if you have gone past the first record.

    .. py:method:: is_valid()

        :rtype: bool

        Indicate whether this cursor is pointing to a valid record.

    .. py:method:: __iter__()

        Iterate over the keys in the database, returning 2-tuples of key/value.

        .. note:: Iteration will begin wherever the cursor is currently pointing, rather than starting at the first record.

    .. py:method:: key()

        Return the key of the current record.

    .. py:method:: value()

        Return the value of the current record.

    .. py:method:: delete()

        Delete the record currently pointed to by the cursor.

        .. warning::
            The :py:meth:`~Cursor.delete` method is a little weird in that
            it only seems to work if you explicitly call :py:meth:`~Cursor.seek`
            beforehand.

    .. py:method:: fetch_until(stop_key[, include_stop_key=True])

        :param str stop_key: The key at which the cursor should stop iterating.
        :param bool include_stop_key: Whether the stop key/value pair should be returned.

        Yield successive key/value pairs until the ``stop_key`` is reached.
        By default the ``stop_key`` and associated value will be returned, but
        this behavior can be controlled using the ``include_stop_key`` flag.


.. py:class:: VM(unqlite, code)

    :param UnQLite unqlite: An :py:class:`UnQLite` instance.
    :param str code: A Jx9 script.

    Python wrapper around an UnQLite virtual machine. The VM is the primary means of executing Jx9 scripts and interacting with the JSON document store.

    VM instances should not be instantiated directly, but created by calling :py:meth:`UnQLite.vm`.

    .. note:: For information on Jx9 scripting, see the `Jx9 docs <http://unqlite.org/jx9.html>`_.

    Example of passing values into a Jx9 script prior to execution, then extracting values afterwards:

    .. code-block:: python

        script = """
            $collection = 'users';
            db_create($collection);
            db_store($collection, $values);
            $users = db_fetch_all($collection);
        """

        # We can pass all sorts of interesting data in to our script.
        values = [
            {'username': 'huey', 'color': 'white'},
            {'username': 'mickey', 'color': 'black'},
        ]

        with db.vm(script) as vm:
            # Set the value of the `values` variable in the Jx9 script:
            vm['values'] = values

            # Execute the script, which creates the collection and stores
            # the two records.
            vm.execute()

            # After execution, we can extract the value of the `users` variable.
            users = vm['users']

            # Jx9 document store assigns a unique 0-based id to each record
            # in a collection. The extracted variable `users` will now equal:
            print users == [
                {'username': 'huey', 'color': 'white', '__id': 0},
                {'username': 'mickey', 'color': 'black', '__id': 1},
            ]  # prints `True`

    When using the VM outside of a context-manager, the following steps
    should be followed:

    1. instantiate :py:class:`VM` with a Jx9 script.
    2. call :py:meth:`VM.compile` to compile the script.
    3. optional: set one or more values to pass to the Jx9 script using
       :py:meth:`VM.set_value` or :py:meth:`VM.set_values`.
    4. call :py:meth:`VM.execute` to execute the script.
    5. optional: read one or more values back from the VM context, for
       example a return value for a function call, using :py:meth:`VM.get_value`.
    6. call :py:meth:`VM.reset` and return to step 4 if you intend to
       re-execute the script, or call :py:meth:`VM.close` to free the VM
       and associated resources.

    .. py:method:: execute()

        Execute the compiled Jx9 script.

    .. py:method:: close()

        Release the VM, deallocating associated memory.

        .. note:: When using the VM as a context manager, this is handled automatically.

    .. py:method:: __enter__()

        Typically the VM should be used as a context manager. The context manager API handles compiling the Jx9 code and releasing the data-structures afterwards.

        .. code-block:: python

            with db.vm(jx9_script) as vm:
                vm.execute()

    .. py:method:: set_value(name, value)

        :param str name: A variable name
        :param value: Value to pass in to the scope of the Jx9 script, which should be either a string, int, float, bool, list, dict, or None (basically a valid JSON type).

        Set the value of a Jx9 variable. You can also use dictionary-style assignment to set the value.

    .. py:method:: set_values(mapping)

        :param dict mapping: Dictionary of name to value to pass in to the Jx9
            script. This method is short-hand for making multiple calls
            to :py:meth:`~VM.set_value`.

        Set multiple Jx9 variables.

    .. py:method:: get_value(name)

        :param str name: A variable name

        Retrieve the value of a variable after the execution of a Jx9 script. You can also use dictionary-style lookup to retrieve the value.

    .. py:method:: compile(code)

        :param str code: A Jx9 script.

        Compile the Jx9 script and initialize the VM.

        .. warning::
            It is not necessary to call this method yourself, as it is called automatically when the VM is used as a context manager.

        .. note::
            This does not execute the code. To execute the code, you must also call :py:meth:`VM.execute`.


.. py:class:: Collection(unqlite, name)

    :param unqlite: a :py:class:`UnQLite` instance
    :param str name: the name of the collection

    Perform common operations on a JSON document collection.

    .. note::
        Rather than instantiating this class directly, use the factory method :py:meth:`UnQLite.collection`.

    Basic operations:

    .. code-block:: pycon

        >>> users = db.collection('users')
        >>> users.create()  # Create the collection if it does not exist.
        >>> users.exists()
        True

        >>> users.store([
        ...     {'name': 'Charlie', 'color': 'green'},
        ...     {'name': 'Huey', 'color': 'white'},
        ...     {'name': 'Mickey', 'color': 'black'}])
        True
        >>> users.store({'name': 'Leslie', 'color': 'also green'})
        True

        >>> users.fetch(0)  # Fetch the first record (user "__id" = 0).
        {'__id': 0, 'color': 'green', 'name': 'Charlie'}

        >>> users.delete(0)  # Delete the first record (user "__id" = 0).
        True
        >>> users.delete(users.last_record_id())  # Delete the last record.
        True

        >>> users.update(1, {'color': 'white', 'name': 'Baby Huey'})
        True

        >>> users.all()
        [{'__id': 1, 'color': 'white', 'name': 'Baby Huey'},
         {'__id': 2, 'color': 'black', 'name': 'Mickey'}]

        >>> for user in users:
        ...     print(user)
        {'__id': 1, 'color': 'white', 'name': 'Baby Huey'}
        {'__id': 2, 'color': 'black', 'name': 'Mickey'}

        >>> users.filter(lambda obj: obj['name'].startswith('B'))
        [{'__id': 1, 'color': 'white', 'name': 'Baby Huey'}]

    .. py:method:: all()

        :returns: list containing all records in the collection.

        As of 0.9.0, it is also possible to iterate the collection using a
        Python iterable. See :py:meth:`~Collection.iterator`.

    .. py:method:: iterator()

        :returns: :py:class:`CollectionIterator` for iterating over the records
            in the collection.

        .. code-block:: pycon

            >>> reg = db.collection('register')
            >>> reg.create()
            >>> reg.store([{'key': 'k0'}, {'key': 'k1'}, {'key': 'k2'}])

            >>> it = reg.iterator()
            >>> for row in it:
            ...     print(row)
            {'__id': 0, 'key': 'k0'}
            {'__id': 1, 'key': 'k1'}
            {'__id': 2, 'key': 'k2'}

            >>> list(it)  # We can re-use the iterator.
            [{'__id': 0, 'key': 'k0'},
             {'__id': 1, 'key': 'k1'},
             {'__id': 2, 'key': 'k2'}]

            >>> for row in reg:  # Iterating over collection is fine, too.
            ...     print(row)
            {'__id': 0, 'key': 'k0'}
            {'__id': 1, 'key': 'k1'}
            {'__id': 2, 'key': 'k2'}

    .. py:method:: filter(filter_fn)

        Filter the list of records using the provided function (or lambda).
        Your filter function should accept a single parameter, which will be
        the record, and return a boolean value indicating whether the record
        should be returned.

        :param filter_fn: callable that accepts record and returns boolean.
        :returns: list of matching records.

        Example:

        .. code-block:: pycon

            >>> users.filter(lambda user: user['is_admin'] == True)
            [{'__id': 0, 'username': 'Huey', 'is_admin': True},
             {'__id': 3, 'username': 'Zaizee', 'is_admin': True},
             {'__id': 4, 'username': 'Charlie', 'is_admin': True}]

    .. py:method:: create()

        Create the collection if it does not exist.

        :returns: true on success, false if collection already exists.

    .. py:method:: drop()

        Drop the collection, deleting all records.

        :returns: true on success, false if collection does not exist.

    .. py:method:: exists()

        :returns: boolean value indicating whether the collection exists.

    .. py:method:: creation_date()

        :returns: the timestamp the collection was created (if exists) or None.

    .. py:method:: set_schema([_schema=None[, **kwargs]])

        Set the schema metadata associated with the collection. The schema is
        **not enforced by the database engine**, and is for metadata purposes.

        :param dict _schema: a mapping of field-name to data-type, or
        :param kwargs: key/value mapping of field to data-type.
        :returns: true on success, false on failure.

    .. py:method:: get_schema()

        Get the schema metadata associated with the collection.

        :returns: mapping of field-name to data-type on success, or None.

    .. py:method:: last_record_id()

        :returns: The integer ID of the last record stored in the collection.

    .. py:method:: current_record_id()

        :returns: The integer ID of the record pointed to by the active cursor.

    .. py:method:: reset_cursor()

        Reset the collection cursor to point to the first record in the collection.

    .. py:method:: __len__()

        Return the number of records in the collection.

    .. py:method:: __iter__()

        Return a :py:class:`CollectionIterator` for iterating over the records
        in the collection.

    .. py:method:: fetch(record_id)

        Return the record with the given id.

        .. code-block:: pycon

            >>> users = db.collection('users')
            >>> users.fetch(0)  # Fetch the first record in collection (id=0).
            {'name': 'Charlie', 'color': 'green', '__id': 0}

            >>> users[1]  # You can also use dictionary-style lookup.
            {'name': 'Huey', 'color': 'white', '__id': 1}

        You can also use the dictionary API:

        .. code-block:: python

            >>> users[0]
            {'name': 'Charlie', 'color': 'green', '__id': 0}

    .. py:method:: store(record[, return_id=True])

        :param record: Either a dictionary (single-record), or a list of dictionaries.
        :param bool return_id: Return the ID of the newly-created object.
        :returns: New object's ID, or a boolean indicating if the record was stored successfully.

        Store the record(s) in the collection.

        .. code-block:: pycon

            >>> users = db.collection('users')
            >>> users.store({'name': 'Charlie', 'color': 'green'})
            True
            >>> users.store([
            ...     {'name': 'Huey', 'color': 'white'},
            ...     {'name': 'Mickey', 'color': 'black'}])
            True

    .. py:method:: update(record_id, record)

        :param record_id: The ID of the record to update.
        :param record: A dictionary of data to update the given record ID.
        :returns: Boolean value indicating if the update was successful.

        Update the data stored for the given ``record_id``. The data is completely replaced, rather than being appended to.

        .. code-block:: pycon

            >>> users = db.collection('users')
            >>> users.store({'name': 'Charlie'})
            True
            >>> users.update(users.last_record_id(), {'name': 'Chuck'})
            True
            >>> users.fetch(users.last_record_id())
            {'__id': 0, 'name': 'Chuck'}

        You can also use dictionary-style assignment using the record ID:

        .. code-block:: pycon

            >>> users[0] = {'name': 'Charles'}  # Can also use item assignment by id.
            >>> users[0]
            {'__id': 0, 'name': 'Charles'}

    .. py:method:: delete(record_id)

        :param record_id: The database-provided ID of the record to delete.
        :returns: Boolean indicating if the record was deleted successfully.

        Delete the record with the given id.

        .. code-block:: pycon

            >>> data = db.collection('data')
            >>> data.create()
            >>> data.store({'foo': 'bar'})
            True
            >>> data.delete(data.last_record_id())
            True
            >>> data.all()
            []

        You can also use the dictionary API:

        .. code-block:: pycon

            >>> del users[1]  # Delete user object with `__id=1`.

    .. py:method:: fetch_current()

        Fetch the record pointed to by the collection cursor.

        ..warning::
            This method does not work as intended as the VM is reset for each
            script execution.


.. py:class:: CollectionIterator(Collection)

    Python iterator that returns rows from a collection. This class should not
    be instantiated directly, but via :py:meth:`Collection.iterator` or
    implicitly by iterating directly over a :py:class:`Collection`.
