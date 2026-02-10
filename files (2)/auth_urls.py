"""
Authentication URL patterns
Add these to your musewave/urls.py file
"""

from django.urls import path
from . import auth_views

# Authentication URL patterns
# Add these to your existing urlpatterns in musewave/urls.py

auth_urlpatterns = [
    # Authentication
    path('users/login/', auth_views.login_view, name='login'),
    path('users/logout/', auth_views.logout_view, name='logout'),
    path('users/refresh/', auth_views.token_refresh_view, name='token_refresh'),
    path('users/verify-token/', auth_views.verify_token_view, name='verify_token'),
    
    # Password management
    path('users/password/change/', auth_views.change_password_view, name='change_password'),
    path('users/password/reset/', auth_views.password_reset_request_view, name='password_reset_request'),
    path('users/password/reset/confirm/', auth_views.password_reset_confirm_view, name='password_reset_confirm'),
]

# To use these, update your musewave/urls.py:
#
# from django.urls import path, re_path
# from . import views
# from . import auth_views
#
# urlpatterns = [
#     # Authentication endpoints
#     path('users/login/', auth_views.login_view, name='login'),
#     path('users/logout/', auth_views.logout_view, name='logout'),
#     path('users/refresh/', auth_views.token_refresh_view, name='token_refresh'),
#     path('users/verify-token/', auth_views.verify_token_view, name='verify_token'),
#     path('users/password/change/', auth_views.change_password_view, name='change_password'),
#     path('users/password/reset/', auth_views.password_reset_request_view, name='password_reset_request'),
#     path('users/password/reset/confirm/', auth_views.password_reset_confirm_view, name='password_reset_confirm'),
#     
#     # ... rest of your existing URLs
# ]
