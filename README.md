UW Canvas Users LTI App
================

A Django LTI application for adding users to Canvas courses aligned with UW policy

Installation
------------

**Project directory**

Install the app in your project.

    $ cd [project]
    $ pip install UW-Canvas-Users-LTI

Project settings.py
------------------

**INSTALLED_APPS**

    'canvas_users',
    'blti',

**REST client app settings**

    RESTCLIENTS_CANVAS_DAO_CLASS='Live'
    RESTCLIENTS_CANVAS_HOST = 'example.instructure.com'
    RESTCLIENTS_CANVAS_OAUTH_BEARER='...'

**BLTI settings**

[django-blti settings](https://github.com/uw-it-aca/django-blti#project-settingspy)

Project urls.py
---------------
    url(r'^canvas_users/', include('canvas_users.urls')),
