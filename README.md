# UW Canvas Users LTI App

[![Build Status](https://github.com/uw-it-aca/django-canvas-users/workflows/Build%2C%20Test%20and%20Deploy/badge.svg?branch=main)](https://github.com/uw-it-aca/django-canvas-users/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/django-canvas-users/badge.svg?branch=main)](https://coveralls.io/github/uw-it-aca/django-canvas-users?branch=main)

A Django LTI application for adding users to Canvas courses aligned with UW policy

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
