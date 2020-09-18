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
        return {'Authorization': 'Bearer {}'.format(bearer_key)}


def validate_logins(logins=[]):
    url = '/ap1/v1/logins'
    headers = {'Accept': 'application/json', 'Connection': 'keep-alive'}

    response = SIS_PROVISIONER_DAO().postURL(url, headers, json.dumps(logins))

    if response.status != 200:
        raise DataFailureException(url, response.status, response.data)

    return json.loads(response.data)
