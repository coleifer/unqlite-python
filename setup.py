from setuptools import Extension
from setuptools import find_packages
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.install import install as InstallCommand

import os
import subprocess

lib_vedis = Extension(
    name='unqlite.libunqlite',
    define_macros=[('UNQLITE_ENABLE_THREADS', '1')],
    sources=['unqlite/src/unqlite.c'])

class GenerateCtypesWrapper(build_py):
    def run(self):
        cur_dir = os.path.realpath(os.path.dirname(__file__))
        wrapper = os.path.join(cur_dir, 'unqlite', '_unqlite.py')
        subprocess.check_call([
            'python',
            os.path.join('ctypesgen', 'ctypesgen.py'),
            os.path.join('unqlite', 'src', 'unqlite.h'),
            '-L',
            './',
            '-l',
            'unqlite',
            '-o',
            wrapper])

        # Read content of generated file.
        with open(wrapper) as fh:
            content = fh.readlines()

        # Modify the add_library_path to use the current dir.
        with open(wrapper, 'w') as fh:
            for line in content:
                if line.startswith('add_library_search_dirs('):
                    fh.write('add_library_search_dirs(['
                             'os.path.realpath(os.path.dirname(__file__))'
                             '])\n')
                else:
                    fh.write(line)

        return build_py.run(self)

setup(
    name='unqlite',
    version='0.2.0',
    description='Python bindings for UnQLite, the embedded NoSQL database.',
    author='Charles Leifer',
    author_email='',
    packages=['unqlite'] + find_packages(),
    package_data={
        'unqlite': [
            'src/unqlite.c',
            'src/unqlite.h',
        ],
    },
    zip_safe=False,
    ext_modules=[lib_vedis],
    cmdclass={'build_py': GenerateCtypesWrapper},
)
