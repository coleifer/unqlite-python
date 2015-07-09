import os

from distutils.core import setup, Extension
from Cython.Build import cythonize


cur_dir = os.path.dirname(__file__)
cython_module = os.path.join(cur_dir, 'unqlite/unqlite.pyx')
c_source = os.path.join(cur_dir, 'unqlite/src/unqlite.c')
unqlite_extension = Extension(
    'unqlite/unqlite',
    sources=[cython_module, c_source])

setup(
    name='unqlite',
    version='0.3.0',
    description='Fast Python bindings for the UnQLite embedded NoSQL database.',
    author='Charles Leifer',
    author_email='',
    packages=['unqlite'],
    ext_modules=cythonize(unqlite_extension),
)
