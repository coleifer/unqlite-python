import glob
import warnings

from setuptools import setup
from setuptools.extension import Extension
try:
    from Cython.Build import cythonize
except ImportError:
    cython_installed = False
    warnings.warn('Cython not installed, using pre-generated C source file.')
else:
    cython_installed = True


if cython_installed:
    python_source = 'unqlite.pyx'
else:
    python_source = 'unqlite.c'
    cythonize = lambda obj: obj

library_source = ['src/unqlite.c']
unqlite_extension = Extension(
    'unqlite',
    sources=[python_source] + library_source)

setup(
    name='unqlite',
    version='0.9.2',
    description='Fast Python bindings for the UnQLite embedded NoSQL database.',
    author='Charles Leifer',
    author_email='',
    url='https://github.com/coleifer/unqlite-python',
    license='MIT',
    install_requires=['Cython'],
    setup_requires=['cython'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: C',
        'Programming Language :: Cython',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    ext_modules=cythonize([unqlite_extension])
)
