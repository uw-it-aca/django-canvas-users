from django.urls import include, re_path

urlpatterns = [
    re_path(r'^', include('canvas_users.urls')),
]
