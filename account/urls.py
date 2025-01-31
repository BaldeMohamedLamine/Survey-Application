from django.urls import path
from django.contrib.auth import views 

from . import views

app_name = "account"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("confirm-email/<str:token>/", views.confirm_email, name="confirm_email"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
    path("request-password-reset/", views.request_password_reset, name="request_password_reset"),
    path("reset-password/<str:token>/", views.reset_password, name="reset_password"),
    path("login/", views.custom_login, name="login"),
    path('logout/', views.logout_view, name='logout'),
]
