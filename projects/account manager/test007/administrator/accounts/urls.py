from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('deleteTokens/', views.deleteTokens, name='deleteTokens'),
    path('generateToken/', views.generateToken, name='generateToken'),
    path('generateIdentifier/', views.generateIdentifier, name='generateIdentifier'),
    #path('login/', views.login, name='login'),
]
