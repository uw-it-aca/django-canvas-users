import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/django-canvas-users>`_.
"""

version_path = 'canvas_users/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='UW-Canvas-Users-LTI',
    version=VERSION,
    packages=['canvas_users'],
    include_package_data=True,
    install_requires = [
        'Django~=4.2',
        'django-blti~=2.2',
        'uw-memcached-clients~=1.0',
        'UW-RestClients-Canvas~=1.2',
    ],
    license='Apache License, Version 2.0',
    description=(
        'Django LTI application for adding users to Canvas courses '
        'aligned with UW policy'),
    long_description=README,
    url='https://github.com/uw-it-aca/django-canvas-users',
    author = "UW-IT T&LS",
    author_email = "aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
