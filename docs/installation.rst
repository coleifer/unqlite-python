.. _installation:

Installation
============

You can use ``pip`` to install ``unqlite``:

.. code-block:: console

    pip install cython unqlite

The project is hosted at https://github.com/coleifer/unqlite-python and can be installed from source:

.. code-block:: console

    git clone https://github.com/coleifer/unqlite-python
    cd unqlite-python
    python setup.py build
    python setup.py install

.. note::
    ``unqlite-python`` depends on `Cython <http://www.cython.org>`_ to generate the Python extension. As of 0.5.0, unqlite-python no longer ships with a generated C source file, so it is necessary to install Cython in order to compile ``unqlite-python``.

After installing unqlite-python, you can run the unit tests by executing the `tests` module:

.. code-block:: console

    python tests.py
