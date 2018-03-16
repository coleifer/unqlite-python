.. unqlite-python documentation master file, created by
   sphinx-quickstart on Mon Jun 16 23:34:38 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

unqlite-python
==============

.. image:: http://media.charlesleifer.com/blog/photos/unqlite-python-logo.png

Fast Python bindings for `UnQLite <http://unqlite.org/>`_, a lightweight, embedded NoSQL database and JSON document store.

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
* Supports both Python 2 and Python 3.

The previous version (0.2.0) of ``unqlite-python`` utilized ``ctypes`` to wrap the UnQLite C library. By switching to Cython, key/value, cursor and Jx9 collection operations are an order of magnitude faster. In particular, filtering collections using user-defined Python functions is now *much*, *much* more performant.

The source code for unqlite-python is `hosted on GitHub <https://github.com/coleifer/unqlite-python>`_.

.. note::
  If you encounter any bugs in the library, please `open an issue <https://github.com/coleifer/unqlite-python/issues/new>`_, including a description of the bug and any related traceback.

.. note::
  If you like UnQLite, you might also want to check out `Vedis <http://vedis.symisc.net>`_, an embedded key/value database modeled after Redis (python bindings: `vedis-python <https://vedis-python.readthedocs.io>`_).

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

