from .base_settings import *
import os

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True

INSTALLED_APPS += [
    'canvas_users.apps.CanvasUsersConfig',
]

if os.getenv('SIS_PROVISIONER_ENV') in RESTCLIENTS_DEFAULT_ENVS:
    RESTCLIENTS_SIS_PROVISIONER_DAO_CLASS = 'Live'
    RESTCLIENTS_SIS_PROVISIONER_TIMEOUT = RESTCLIENTS_DEFAULT_TIMEOUT
    RESTCLIENTS_SIS_PROVISIONER_POOL_SIZE = RESTCLIENTS_DEFAULT_POOL_SIZE
    RESTCLIENTS_SIS_PROVISIONER_OAUTH_BEARER = os.getenv('SIS_PROVISIONER_OAUTH_BEARER', '')
    if os.getenv('SIS_PROVISIONER_ENV') == 'PROD':
        RESTCLIENTS_SIS_PROVISIONER_HOST = 'https://apps.canvas.uw.edu'
    else:
        RESTCLIENTS_SIS_PROVISIONER_HOST = 'https://test-apps.canvas.uw.edu'

CONTINUUM_CANVAS_ACCOUNT_ID = os.getenv('CONTINUUM_CANVAS_ACCOUNT_ID', '')
