#!/usr/bin/env python3

import sys
from distutils.core import setup

if sys.version_info < (3, 7):
    print('Only python >3.7 supported.', file=sys.stderr)
    sys.exit(1)

setup(
    name='foxi',
    author='Olmo Kramer',
    author_email='olmo.kramer@protonmail.com',
    version='0.1.0',
    description='Theorem prover in theory of meadows.',
    long_description='Theorem prover in theory of meadows.',
    packages=['foxi'],
    entry_points={
        'console_scripts': [
	    'foxi = foxi.__main__:main',
        ],
    },
    install_requires=[
        'sympy',
    ],
)
