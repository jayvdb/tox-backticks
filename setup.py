#!/usr/bin/env python

from setuptools import setup

classifiers = """\
Environment :: Console
Framework :: tox
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Operating System :: OS Independent
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Quality Assurance
Topic :: Software Development :: Testing
Development Status :: 4 - Beta
"""

setup(
    name='tox-backticks',
    version='0.2.0',
    description='Tox plugin to allow use of backticks for subcommands',
    license='MIT',
    author_email='jayvdb@gmail.com',
    url='https://github.com/jayvdb/tox-backticks',
    py_modules=['tox_backticks'],
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=[
        'tox >= 3.8',
    ],
    entry_points={'tox': ['backticks = tox_backticks']},
    classifiers=classifiers.splitlines(),
    tests_require=['tox'],
)
