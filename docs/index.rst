.. unqlite-python documentation master file, created by
   sphinx-quickstart on Mon Jun 16 23:34:38 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

unqlite-python
==============

.. image:: http://media.charlesleifer.com/blog/photos/unqlite-python-logo.png

Fast Python bindings for `UnQLite <http://unqlite.org/>`_, a lightweight, embedded NoSQL database and JSON document store.

.. warning::
    Read the issue tracker for `this database <https://github.com/symisc/unqlite/issues/>`_
    before considering using it. UnQLite has not seen any meaningful development
    since 2014. It is **strongly** recommended that you use `Sqlite <https://www.sqlite.org/>`_.
    Sqlite has robust support for `json <https://www.sqlite.org/json1.html>`_ and is
    actively developed and maintained.

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

The source code for unqlite-python is `hosted on GitHub <https://github.com/coleifer/unqlite-python>`_.

.. note::
  If you encounter any bugs in the library, please `open an issue <https://github.com/coleifer/unqlite-python/issues/new>`_, including a description of the bug and any related traceback.

Contents:

.. toctree::
   :maxdepth: 2
   :glob:

   installation
   quickstart
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

