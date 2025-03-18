# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from canvas_users.views import LaunchView, AddUsersView
from canvas_users.views.api.account import CanvasAccountCourseRoles
from canvas_users.views.api.course import (
    ValidCanvasCourseUsers, ImportCanvasCourseUsers)
from canvas_users.views.api.section import CanvasCourseSections


urlpatterns = [
    re_path(r'^$', LaunchView.as_view()),
    re_path(r'^users/add$', AddUsersView.as_view()),
    re_path((
        r'^users/api/v1/canvas/account/'
        r'(?P<canvas_account_id>[0-9]+)/course/roles$'),
        CanvasAccountCourseRoles.as_view()),
    re_path(
        r'^users/api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/sections$',
        CanvasCourseSections.as_view()),
    re_path(
        r'^users/api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/validate$',
        ValidCanvasCourseUsers.as_view()),
    re_path(
        r'^users/api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/import$',
        ImportCanvasCourseUsers.as_view()),
]
