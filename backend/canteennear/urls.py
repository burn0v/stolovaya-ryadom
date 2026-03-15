from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path("canteen/<int:id>/", views.canteen_detail, name="canteen_detail"),
]
