#!/usr/bin/env python

import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-canvas-users',
    version='0.1',
    packages=['canvas_users'],
    include_package_data=True,
    install_requires = [
        'setuptools',
        'django==1.7.11',
        'django-compressor',
        'django-templatetag-handlebars'
    ],
    license='Apache License, Version 2.0',  # example license
    description='Django application for adding users to Canvas courses aligned with UW policy',
    long_description=README,
    url='https://github.com/uw-it-aca/django-canvas-users',
    author = "UW-IT ACA",
    author_email = "mikes@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
