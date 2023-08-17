from .base_settings import *
import os

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True
else:
    RESTCLIENTS_DAO_CACHE_CLASS = 'canvas_users.cache.RestclientsCache'

INSTALLED_APPS += [
    'canvas_users.apps.CanvasUsersConfig',
    'django_extensions',
]

if os.getenv('ENV', 'localdev') == 'test':
    DATABASES['postgres'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '172.18.1.43',
        'PORT': '5432',
        'NAME': os.getenv('DATABASE_DB_NAME', 'db'),
        'USER': os.getenv('DATABASE_USERNAME', None),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', None),
    }

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

COURSE_ROLES_EXPIRES = 60 * 60 * 24 * 30

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'stdout_stream': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: record.levelno < logging.WARNING
        },
        'stderr_stream': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: record.levelno > logging.ERROR
        }
    },
    'formatters': {
        'default': {
            'format': '%(levelname)-4s %(asctime)s %(module)s %(message)s [%(name)s]',
            'datefmt': '[%Y-%m-%d %H:%M:%S]',
        },
        'restclients_timing': {
            'format': '%(levelname)-4s restclients_timing %(module)s %(asctime)s %(message)s [%(name)s]',
            'datefmt': '[%Y-%m-%d %H:%M:%S]',
        },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'filters': ['stdout_stream'],
            'formatter': 'default',
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'filters': ['stderr_stream'],
            'formatter': 'default',
        },
        'restclients_timing': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'filters': ['stdout_stream'],
            'formatter': 'restclients_timing',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'django.request': {
            'handlers': ['stderr'],
            'level': 'ERROR',
            'propagate': True,
        },
        'canvas_users': {
            'handlers': ['stdout'],
            'level': 'INFO',
            'propagate': True,
        },
        'restclients_core': {
            'handlers': ['restclients_timing'],
            'level': 'INFO',
            'propagate': False,
        },
        'blti': {
            'handlers': ['stdout'],
            'level': 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['stdout', 'stderr'],
            'level': 'INFO' if os.getenv('ENV', 'localdev') == 'prod' else 'DEBUG'
        }
    }
}
