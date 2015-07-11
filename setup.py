import os

from distutils.core import setup, Extension
try:
    from Cython.Build import cythonize
except ImportError:
    import warnings
    cython_installed = False
    warnings.warn('Cython not installed, using pre-generated C source file.')
else:
    cython_installed = True


if cython_installed:
    python_source = 'unqlite.pyx'
else:
    python_source = 'unqlite.c'
    cythonize = lambda obj: [obj]
library_source = 'src/unqlite.c'

unqlite_extension = Extension(
    'unqlite',
    sources=[python_source, library_source])

setup(
    name='unqlite',
    version='0.4.1',
    description='Fast Python bindings for the UnQLite embedded NoSQL database.',
    author='Charles Leifer',
    author_email='',
    ext_modules=cythonize(unqlite_extension),
)
