from rc_django.cache_implementation.memcache import MemcachedCache
import re

ONE_MINUTE = 60
ONE_WEEK = 60 * 60 * 24 * 7


class IDCardPhotoCache(MemcachedCache):
    def get_cache_expiration_time(self, service, url):
        if 'canvas' == service:
            if re.match(r'^/api/v\d/accounts/\d+/roles', url):
                return ONE_WEEK
            return ONE_MINUTE
