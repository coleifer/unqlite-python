import os

from distutils.core import setup, Extension
try:
    from Cython.Build import cythonize
except ImportError:
    raise RuntimeError('Cython must be installed in order to build '
                       'unqlite-python.')


cython_module = 'unqlite.pyx'
c_source = 'src/unqlite.c'
unqlite_extension = Extension(
    'unqlite',
    sources=[cython_module, c_source])

setup(
    name='unqlite',
    version='0.3.2',
    description='Fast Python bindings for the UnQLite embedded NoSQL database.',
    author='Charles Leifer',
    author_email='',
    ext_modules=cythonize(unqlite_extension),
)
