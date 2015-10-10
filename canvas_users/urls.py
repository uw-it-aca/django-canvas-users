from django.conf.urls import patterns, url, include
from canvas_users.views import CanvasUsers
from canvas_users.views.api.account import CanvasAccountCourseRoles
from canvas_users.views.api.course import CanvasCourseSections, ValidCanvasCourseUsers
    


urlpatterns = patterns('',
    url(r'^$', CanvasUsers),
    url(r'api/v1/canvas/account/(?P<canvas_account_id>[0-9]+)/course/roles$', CanvasAccountCourseRoles().run),
    url(r'api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/sections$', CanvasCourseSections().run),
    url(r'api/v1/canvas/course/(?P<canvas_course_id>[0-9]+)/validate$', ValidCanvasCourseUsers().run),
)
