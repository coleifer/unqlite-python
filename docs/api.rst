.. _api:

API Documentation
=================

.. py:class:: UnQLite([database=':mem:'[, open_manually=False]])

    The :py:class:`UnQLite` object provides a pythonic interface for interacting
    with `UnQLite databases <http://unqlite.symisc.net/>`_. UnQLite is a lightweight,
    embedded NoSQL database and JSON document store.

    :param str database: The path to the database file.
    :param bool open_manually: If set to ``True``, the database will not be
        opened automatically upon instantiation and must be opened by a call
        to :py:meth:`~UnQLite.open`.

    .. note::
        UnQLite supports in-memory databases, which can be created by passing
        in ``':mem:'`` as the database file. This is the default behavior if
        no database file is specified.

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

        >>> with db.compile_script(script) as vm:
        ...     vm['list_of_users'] = list_of_users
        ...     vm.execute()
        ...     users_from_db = vm['users_from_db']
        ...
        True

        >>> users_from_db  # UnQLite assigns items in a collection an ID.
        [{'username': 'Huey', 'age': 3, '__id': 0},
         {'username': 'Mickey', 'age': 5, '__id': 1}]

    .. py:method:: open([flags=UNQLITE_OPEN_CREATE])

        :param flags: Optional flags to use when opening the database.
        :raises: ``Exception`` if an error occurred opening the database.

        Open the database connection. This method should only be called if the
        database was manually closed, or if the database was instantiated with
        ``open_manually=True``.

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

        :raises: ``Exception`` if an error occurred closing the database.

        Close the database connection.

    .. py:method:: config(verb, \*args)

        :param int verb: A flag indicating what is being configured
        :param args: Verb-specific arguments

        Configure an attribute of the UnQLite database. The list of verbs and their
        parameters can be found in the `unqlite_config docs <http://unqlite.org/c_api/unqlite_config.html>`_.

    .. py:method:: store(key, value)

        Store a value in the given key.

        :param str key: Identifier used for storing data.
        :param any value: A value to store in UnQLite.

        Example:

        .. code-block:: python

            db = UnQLite()
            db.store('some key', 'some value')
            db.store('another key', 'another value')

        You can also use the dictionary-style ``[key] = value`` to store a value:

        .. code-block:: python

            db['some key'] = 'some value'

    .. py:method:: store_fmt(key, value, \*params)

        Like :py:meth:`~UnQLite.store`, except that the ``value`` parameter is a
        ``printf()``-style formatting string.

        Example:

        .. code-block:: python

            db.store_fmt('greeting', 'hello %s, you are %d years old', 'huey', 3)

    .. py:method:: store_file(key, filename)

        Store the contents of a file in the given key. The method uses ``mmap`` to
        create a read-only memory-view of the file, which is then used to store the
        file contents in the database.

        Example:

        .. code-block:: python

            for mp3_file in glob.glob('music/*.mp3'):
                db.store_file(os.path.basename(mp3_file), mp3_file)

    .. py:method:: append(key, value)

        Append the given ``value`` to the data stored in the ``key``. If no data exists, the operation
        is equivalent to :py:meth:`~UnQLite.store`.

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

    .. py:method:: fetch(key)

        Retrieve the value stored at the given ``key``. If no value exists,
        a ``KeyError`` will be raised.

        :param str key: Identifier to retrieve
        :returns: The data stored at the given key
        :raises: ``KeyError`` if the given key does not exist.

        Example:

        .. code-block:: python

            db = UnQLite()
            db.store('some key', 'some value')
            value = db.fetch('some key')

        You can also use the dictionary-style ``[key]`` lookup to retrieve a value:

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

    .. py:method:: compile_script(code)

        :param str code: a Jx9 script.
        :returns: a context manager yielding a :py:class:`VM` instance.

        Compile the given Jx9 script and return an initialized :py:class:`VM` instance.

        Usage:

        .. code-block:: python

            script = "$users = db_fetch_all('users');"
            with db.compile_script(script) as vm:
                vm.execute()
                users = vm['users']

    .. py:method:: compile_file(filename)

        :param str filename: filename of Jx9 script
        :returns: a context manager yielding a :py:class:`VM` instance.

        Compile the given Jx9 file and return an initialized :py:class:`VM` instance.

        Usage:

        .. code-block:: python

            with db.compile_file('myscript.jx9') as vm:
                vm.execute()

    .. py:method:: collection(name)

        :param str name: The name of the collection.

        Factory method for instantiating a :py:class:`Collection` for working
        with a collection of JSON objects.

        Usage:

        .. code-block:: python

            Users = db.collection('users')

            # Fetch all records in the collection.
            all_users = Users.all()

            # Create a new record.
            Users.store({'name': 'Charlie', 'activities': ['reading', 'programming']})

        See the :py:class:`Collection` docs for more examples.

    .. py:method:: VM()

        :returns: an uninitialized :py:class:`VM` instance.

        Create a VM instance which can then be used to compile and
        execute Jx9 scripts.

        .. code-block:: python

            with db.VM() as vm:
                vm.compile(my_script)
                vm.execute()

    .. py:method:: cursor()

        :returns: a :py:class:`Cursor` instance.

        Create a cursor for traversing database records.

    .. py:method:: range(start_key, end_key[, include_end_key=True])

        Iterate over a range of key/value pairs in the database.

        .. code-block:: python

            for key, value in db.range('d.20140101', 'd.20140201', False):
                calculate_daily_aggregate(key, value)

    .. py:method:: random_string(nbytes)

        :param int nbytes: number of bytes to generate
        :returns: a string consisting of random lower-case letters (a-z).

    .. py:method:: random_number()

        :returns: a random positive integer


.. py:class:: Cursor(unqlite)

    :param unqlite: A pointer to an unqlite struct.

    Create and initialize a cursor. Cursors can be used as context managers,
    which ensures that they are closed.

    Rather than instantiating this class directly, it is preferable to call
    the factory method :py:meth:`UnQLite.cursor`.

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

    .. py:method:: close()

        Close and release the database cursor.

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

    .. py:method:: is_valid()

        :rtype: bool

        Indicate whether this cursor is pointing to a valid record, or has
        reached the end of the database.

    .. py:method:: next()

        Move the cursor to the next record.

    .. py:method:: previous()

        Move the cursor to the previous record.

    .. py:method:: reset()

        Reset the cursor, which also resets the pointer to the first record.

    .. py:method:: delete()

        Delete the record currently pointed to by the cursor.

        .. warning::
            The :py:meth:`~Cursor.delete` method is a little weird in that
            it only seems to work if you explicitly call :py:meth:`~Cursor.seek`
            beforehand.

    .. py:method:: key()

        Return the key of the current record.

    .. py:method:: value()

        Return the value of the current record.

    .. py:method:: __iter__()

        Cursors support the Python iteration protocol. Successive iterations
        yield key/value pairs.

    .. py:method:: fetch_count(ct)

        :param int ct: Number of rows to fetch.

        Iterate from the current record, yielding the next ``ct`` key/value
        pairs.

    .. py:method:: fetch_until(stop_key[, include_stop_key=True])

        :param str stop_key: The key at which the cursor should stop iterating.
        :param bool include_stop_key: Whether the stop key/value pair should be returned.

        Yield successive key/value pairs until the ``stop_key`` is reached.
        By default the ``stop_key`` and associated value will be returned, but
        this behavior can be controlled using the ``include_stop_key`` flag.


.. py:class:: VM(unqlite)

    :param unqlite: A pointer to an unqlite struct.

    Python wrapper around an UnQLite virtual machine. The VM is the primary
    means of executing Jx9 scripts and interacting with the JSON document
    store.

    VM instances will rarely be created explicitly. Instead, they are yielded
    by calls to :py:meth:`UnQLite.compile_script` and :py:meth:`UnQLite.compile_file`.
    Rather than instantiating this class directly, it is preferable to call
    the factory method :py:meth:`UnQLite.VM`.

    .. note:: For information on Jx9 scripting, see the `Jx9 docs <http://unqlite.org/jx9.html>`_.

    Example of passing values into a Jx9 script prior to execution, then extracting
    values afterwards:

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

        with self.db.compile_script(script) as vm:
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

    .. py:method:: compile(code)

        :param str code: A Jx9 script.

        Compile the Jx9 script and initialize the VM.

        .. note::
            This does not execute the code. To execute the code, you
            must also call :py:meth:`VM.execute`.

    .. py:method:: compile_file(filename)

        :param str code: The filename of a Jx9 script.

        Compile the Jx9 script file and initialize the VM.

        .. note::
            This does not execute the code. To execute the code, you
            must also call :py:meth:`VM.execute`.

    .. py:method:: close()

        Release the VM, deallocating associated memory. When using the VM
        as a context manager, this is handled automatically.

    .. py:method:: reset()

        Reset the VM.

    .. py:method:: execute()

        Execute the compiled Jx9 bytecode.

    .. py:method:: config(verb, \*args)

        :param int verb: A flag indicating what is being configured
        :param args: Verb-specific arguments

        Configure an attribute of the VM. The list of verbs and their
        parameters can be found in the `unqlite_vm_config docs <http://unqlite.org/c_api/unqlite_vm_config.html>`_.

    .. py:method:: set_value(name, value)

        :param str name: A variable name
        :param value: Value to pass in to the Jx9 script, which should be either
          a string, int, float, bool, list, dict, or None (basically a valid
          JSON type).

        Set the value of a Jx9 variable. You can also use dictionary-style assignment
        to set the value.

    .. py:method:: extract(name)

        :param str name: A variable name

        Extract the value of a variable after the execution of a Jx9 script. You can also
        use dictionary-style lookup to retrieve the value.

    .. py:method:: foreign_function(name)

        :param str name: Name of foreign function.

        Function decorator for creating foreign functions that are callable from Jx9
        scripts. Your function should have the following signature:

        .. code-block:: python

            def my_foreign_function(context, *args):
                pass

        Return values from your function will automatically be converted into
        Jx9 values.

    .. py:method:: delete_foreign_function(name)

        :param str name: Name of foreign function

        Delete the reference to a foreign function that was previously created
        using the :py:meth:`~VM.foreign_function` decorator.


.. py:class:: Collection(unqlite, name):

    :param unqlite: a :py:class:`UnQLite` instance
    :param str name: the name of the collection

    Perform common operations on a JSON document collection.

    .. note::
        Rather than instantiating this class directly, use the factory
        method :py:meth:`UnQLite.collection`.

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

        >>> users.fetch(0)  # Fetch the first record.
        {'__id': 0, 'color': 'green', 'name': 'Charlie'}

        >>> users.delete(0)  # Delete the first record.
        True
        >>> users.delete(users.last_record_id())  # Delete the last record.
        True

        >>> users.all()
        [{'__id': 1, 'color': 'white', 'name': 'Huey'},
         {'__id': 2, 'color': 'black', 'name': 'Mickey'}]

        >>> users.filter(lambda obj: obj['name'].startswith('H'))
        [{'__id': 1, 'color': 'white', 'name': 'Huey'}]

    .. py:method:: all()

        Return a list containing all records in the collection.

    .. py:method:: filter(filter_fn)

        Filter the list of records using the provided function (or lambda).
        Your filter function should accept a single parameter, which will be
        the record, and return a boolean value indicating whether the record
        should be returned.

    .. py:method:: create()

        Create the collection if it does not exist.

    .. py:method:: drop()

        Drop the collection, deleting all records.

    .. py:method:: exists()

        :returns: boolean value indicating whether the collection exists.

    .. py:method:: last_record_id()

        :returns: The integer ID of the last record stored in the collection.

    .. py:method:: current_record_id()

        :returns: The integer ID of the record pointed to by the active cursor.

    .. py:method:: reset_cursor()

        Reset the collection cursor to point to the first record in the collection.

    .. py:method:: delete(record_id)

        Delete the record with the given id.

    .. py:method:: fetch(record_id)

        Return the record with the given id.

        .. code-block:: pycon

            >>> users = db.collection('users')
            >>> users.fetch(0)  # Fetch the first record in the collection
            {'name': 'Charlie', 'color': 'green', '__id': 0}

            >>> users[1]  # You can also use dictionary-style lookup.
            {'name': 'Huey', 'color': 'white', '__id': 1}

    .. py:method:: store(record)

        :param record: Either a dictionary (single-record), or a list of dictionaries.

        Store the record(s) in the collection.

        .. code-block:: pycon

            >>> users = db.collection('users')
            >>> users.store({'name': 'Charlie', 'color': 'green'})
            >>> users.store([
            ...     {'name': 'Huey', 'color': 'white'},
            ...     {'name': 'Mickey', 'color': 'black'}])

    .. py:method:: fetch_current()

        Fetch the record pointed to by the collection cursor.
