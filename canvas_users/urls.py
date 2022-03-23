# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from django.conf.urls import url
from canvas_users.views import LaunchView, AddUsersView
from canvas_users.views.api.account import CanvasAccountCourseRoles
from canvas_users.views.api.course import (
    ValidCanvasCourseUsers, ImportCanvasCourseUsers)
from canvas_users.views.api.section import CanvasCourseSections


urlpatterns = [
    url(r'^$', LaunchView.as_view()),
    url(r'add$', AddUsersView.as_view()),
    url(r'api/v1/canvas/account/(?P<canvas_account_id>[0-9]+)/course/roles$',
        CanvasAccountCourseRoles.as_view()),
    url(r'api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/sections$',
        CanvasCourseSections.as_view()),
    url(r'api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/validate$',
        ValidCanvasCourseUsers.as_view()),
    url(r'api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/import$',
        ImportCanvasCourseUsers.as_view()),
]
