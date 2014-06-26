![](http://media.charlesleifer.com/blog/photos/unqlite-python.png)

Python bindings for [UnQLite](http://unqlite.symisc.net), a lightweight, embedded NoSQL database and JSON document store.

UnQLite features:

* Embedded, zero-conf database
* Transactional (ACID)
* Single file or in-memory database
* Key/value store
* Cursor support and linear record traversal
* JSON document store
* Thread-safe
* Terabyte-sized databases

Links:

* [unqlite-python documentation](http://unqlite-python.readthedocs.org/)
* [UnQLite's C API](http://unqlite.symisc.net/c_api.html)

## Installation

You can install unqlite using `pip`.

    pip install unqlite

## Basic usage

First you instantiate an `UnQLite` object, passing in either the path to the database file or the special string `':mem:'` for an in-memory database.

Below is a sample interactive console session designed to show some of the basic features and functionality of the unqlite-python library. Also check out the [full API documentation](http://unqlite-python.readthedocs.org/en/latest/api.html).

To begin, instantiate an ``UnQLite`` object. You can specify either the path to a database file, or use UnQLite as an in-memory database.

```pycon
>>> from unqlite import UnQLite
>>> db = UnQLite()  # Create an in-memory database.
```

### Key/value features

UnQLite can be used as a key/value store.

```pycon
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
```

You can also use cursors to traverse the database in key-order:

```pycon
>>> with db.cursor() as cursor:
...     for key, value in cursor:
...         print key, '=>', value
...
foo => bar
k0 => 0
k1 => 1
k2 => 2XXXX
```

There are many different ways of interacting with cursors, which are described in the [Cursor API documentation](http://unqlite-python.readthedocs.org/en/latest/api.html#Cursor).

### Document store features

UnQLite can be used as a JSON document store. The [Jx9 scripting language](http://unqlite.org/jx9.html) is used to interact with the document store.

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

>>> with db.compile_script(script) as vm:
...     vm['list_of_users'] = list_of_users
...     vm.execute()
...     users_from_db = vm['users_from_db']
...
True

>>> users_from_db  # UnQLite assigns items in a collection an ID.
[{'username': 'Huey', 'age': 3, '__id': 0},
 {'username': 'Mickey', 'age': 5, '__id': 1}]
```

More information can be found in the [VM API documentation](http://unqlite-python.readthedocs.org/en/latest/api.html#VM).

-------------------------------------------

This code is based in part on nobonobo's [unqlitepy](https://github.com/nobonobo/unqlitepy) library.
