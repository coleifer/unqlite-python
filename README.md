![](http://media.charlesleifer.com/blog/photos/unqlite-python-logo.png)

Fast Python bindings for [UnQLite](http://unqlite.org/), a lightweight, embedded NoSQL database and JSON document store.

### Please note

**Read the issue tracker for [this database](https://github.com/symisc/unqlite/issues/)**
before considering using it. UnQLite has not seen any meaningful development
since 2014. It is **strongly** recommended that you use [Sqlite](https://www.sqlite.org/).
Sqlite has robust support for [json](https://www.sqlite.org/json1.html) and is
actively developed and maintained.

### Features

UnQLite features:

* Embedded, zero-conf database
* Transactional (ACID)
* Single file or in-memory database
* Key/value store
* Cursor support and linear record traversal
* JSON document store
* Thread-safe
* Terabyte-sized databases

UnQLite-Python features:

* Compiled library, extremely fast with minimal overhead.
* Supports key/value operations, cursors, and transactions using Pythonic APIs.
* Support for Jx9 scripting.
* APIs for working with Jx9 JSON document collections.

Links:

* [unqlite-python documentation](https://unqlite-python.readthedocs.io/)
* [UnQLite's C API](http://unqlite.symisc.net/c_api.html)

## Installation

You can install unqlite using `pip`.

    pip install unqlite

## Basic usage

Below is a sample interactive console session designed to show some of the basic features and functionality of the unqlite-python library. Also check out the [full API documentation](https://unqlite-python.readthedocs.io/en/latest/api.html).

To begin, instantiate an ``UnQLite`` object. You can specify either the path to a database file, or use UnQLite as an in-memory database.

```pycon
>>> from unqlite import UnQLite
>>> db = UnQLite()  # Create an in-memory database.
```

### Key/value features

UnQLite can be used as a key/value store.

```pycon
>>> db['foo'] = 'bar'  # Use as a key/value store.
>>> db['foo']  # The key/value store deals in byte-strings.
b'bar'

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
b'2XXXX'
```

The database can also be iterated through directly. Note that keys are decoded
while values are left as bytestrings.

```pycon
>>> [item for item in db]
[('foo', b'bar'), ('k0', b'0'), ('k1', b'1'), ('k2', b'2XXXX')]
```

### Cursors

For finer-grained record traversal, you can use cursors.

```pycon
>>> with db.cursor() as cursor:
...     cursor.seek('k0')
...     for key, value in cursor:
...         print(key, '=>', value.decode('utf8'))
...
k0 => 0
k1 => 1
k2 => 2XXXX

>>> with db.cursor() as cursor:
...     cursor.seek('k2')
...     print(cursor.value())
...
b'2XXXX'

>>> with db.cursor() as cursor:
...     cursor.seek('k0')
...     print(list(cursor.fetch_until('k2', include_stop_key=False)))
...
[('k0', b'0'), ('k1', b'1')]
```

There are many different ways of interacting with cursors, which are described in the [Cursor API documentation](https://unqlite-python.readthedocs.io/en/latest/api.html#Cursor).

### Document store features

In my opinion the most interesting feature of UnQLite is its JSON document store. The [Jx9 scripting language](http://unqlite.org/jx9.html) is used to interact with the document store, and it is a wacky mix of PHP and maybe JavaScript (?).

**Note**: as of v0.8.0 the document store and collections APIs treat all
strings as unicode.

Interacting with the document store basically consists of creating a Jx9 script (you might think of it as an imperative SQL query), compiling it, and then executing it.

```pycon
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
```

This is just a taste of what is possible with Jx9. In the near future I may add some wrappers around common Jx9 collection operations, but for now hopefully it is not too difficult to work with.

More information can be found in the [VM API documentation](https://unqlite-python.readthedocs.io/en/latest/api.html#VM).

### Collections

To simplify working with JSON document collections, `unqlite-python` provides a light API for
executing Jx9 queries on collections. A collection is an ordered list of JSON objects
(records). Records can be appended or deleted, and in the next major release of UnQLite there will
be support for updates as well.

To begin working with collections, you can use the factory method on ``UnQLite``:

```pycon
>>> users = db.collection('users')
>>> users.create()  # Create the collection if it does not exist.
>>> users.exists()
True
```

You can use the ``store()`` method to add one or many records. To add a single record just pass in a python ``dict``. To add multiple records, pass in a list of dicts. Records can be fetched and deleted by ID.

By default, the ID of the last-stored record is returned. At the time of
writing, IDs start at 0, so when inserting 3 records the last-id is 2:

```pycon
>>> users.store([
...     {'name': 'Charlie', 'color': 'green'},
...     {'name': 'Huey', 'color': 'white'},
...     {'name': 'Mickey', 'color': 'black'}])
2
>>> users.store({'name': 'Leslie', 'color': 'also green'}, return_id=False)
True

>>> users.fetch(0)  # Fetch the first record.
{'__id': 0, 'color': 'green', 'name': 'Charlie'}

>>> users.delete(0)  # Delete the first record.
True
>>> users.delete(users.last_record_id())  # Delete the last record.
True
```

You can retrieve all records in the collection, or specify a filtering function. The filtering function will be registered as a foreign function with the Jx9 VM and called *from* the VM.

```pycon
>>> users.all()
[{'__id': 1, 'color': 'white', 'name': 'Huey'},
 {'__id': 2, 'color': 'black', 'name': 'Mickey'}]

>>> users.filter(lambda obj: obj['name'].startswith('H'))
[{'__id': 1, 'color': 'white', 'name': 'Huey'}]
```

### Transactions

UnQLite supports transactions for file-backed databases (since transactions occur at the filesystem level, they have no effect on in-memory databases).

The easiest way to create a transaction is with the context manager:

```pycon
>>> db = UnQLite('/tmp/test.db')
>>> with db.transaction():
...     db['k1'] = 'v1'
...     db['k2'] = 'v2'
...
>>> db['k1']
b'v1'
```

You can also use the transaction decorator which will wrap a function call in a transaction and commit upon successful execution (rolling back if an exception occurs).

```pycon
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
    return fn(*args, **kwargs)
  File "<stdin>", line 5, in save_value
Exception: uh-oh
>>> db['k3']
b'v3'
```

For finer-grained control you can call `db.begin()`, `db.rollback()` and `db.commit()` manually:

```pycon
>>> db.begin()
>>> db['k3'] = 'v3-xx'
>>> db.commit()
True
>>> db['k3']
b'v3-xx'
```

-------------------------------------------

This code is based in part on [buaabyl's pyUnQLite](https://github.com/buaabyl/pyUnQLite/).
