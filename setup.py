# -*- coding: utf-8 -*-
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='slapddgen',
    author='Daniele Sluijters',
    author_email='daenney@users.noreply.github.com',
    description='slapd.d generator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/daenney/slapddgen',
    version='0.1.1',
    py_modules=['slapddgen'],
    include_package_data=True,
    install_requires=[
        'Click',
        'jinja2',
    ],
    entry_points='''
        [console_scripts]
        slapddgen=slapddgen:cli
    ''',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP',
        'Topic :: Utilities',
    ],
)
