from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('admin/', admin.site.urls),
    path("search/", views.search, name="search"),
    path(
        "reviews/",
        views.EstablishmentsWithReviewsView.as_view(),
        name="reviews_list",
    ),
    path("canteen/<int:id>/", views.canteen_detail, name="canteen_detail"),
    path("register/", views.register, name="register"),
    path('accounts/', include('django.contrib.auth.urls')),
]
