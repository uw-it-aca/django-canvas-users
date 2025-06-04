# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.apps import AppConfig
from restclients_core.dao import MockDAO
import os


class CanvasUsersConfig(AppConfig):
    name = 'canvas_users'

    def ready(self):
        mock_path = os.path.join(os.path.dirname(__file__), "resources")
        MockDAO.register_mock_path(mock_path)
