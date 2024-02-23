# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf import settings
from memcached_clients import RestclientPymemcacheClient
import re


class RestclientsCache(RestclientPymemcacheClient):
    def get_cache_expiration_time(self, service, url, status=200):
        if 'canvas' == service:
            if re.match(r'^/api/v\d/accounts/\d+/roles', url):
                return getattr(settings, 'COURSE_ROLES_EXPIRES', 86400)
            return 60
