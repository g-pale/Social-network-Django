from django.urls import path
from . import views

app_name = 'followers'

urlpatterns = [
    path('toggle/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('followers/<str:username>/', views.followers_list, name='followers_list'),
    path('following/<str:username>/', views.following_list, name='following_list'),
]
