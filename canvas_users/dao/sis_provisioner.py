# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from restclients_core.dao import DAO
from restclients_core.exceptions import DataFailureException
from os.path import abspath, dirname
import os
import json


class SIS_PROVISIONER_DAO(DAO):
    def service_name(self):
        return 'sis_provisioner'

    def service_mock_paths(self):
        return [abspath(os.path.join(dirname(__file__), 'resources'))]

    def _custom_headers(self, method, url, headers, body):
        bearer_key = self.get_service_setting('OAUTH_BEARER', '')
        return {'Authorization': 'Token {}'.format(bearer_key)}


def validate_logins(logins=[]):
    url = '/api/v1/logins'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Connection': 'keep-alive'
    }
    body = {'logins': logins}

    response = SIS_PROVISIONER_DAO().postURL(url, headers, json.dumps(body))

    if response.status != 200:
        raise DataFailureException(url, response.status, response.data)

    data = json.loads(response.data)
    return data.get('users')
