.. _installation:

Installation
============

You can use ``pip`` to install ``unqlite``:

.. code-block:: console

    pip install Cython  # required to compile Python extension.
    pip install unqlite

The project is hosted at https://github.com/coleifer/unqlite-python and can be installed from source:

.. code-block:: console

    git clone https://github.com/coleifer/unqlite-python
    cd unqlite-python
    python setup.py build
    python setup.py install

.. warning::
    ``unqlite-python`` depends on `Cython <http://www.cython.org>`_ to compile the Python extension. Make sure you have Cython installed before installing ``unqlite-python``.

After installing unqlite-python, you can run the unit tests by executing the `unqlite.tests` module:

.. code-block:: console

    python unqlite/tests.py
