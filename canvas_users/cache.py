from django.conf import settings
from rc_django.cache_implementation.memcache import MemcachedCache
import re


class RestclientsCache(MemcachedCache):
    def get_cache_expiration_time(self, service, url):
        if 'canvas' == service:
            if re.match(r'^/api/v\d/accounts/\d+/roles', url):
                return getattr(settings, 'COURSE_ROLES_EXPIRES', 86400)
            return 60
