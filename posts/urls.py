from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/edit/', views.edit, name='edit'),
    path('<int:pk>/delete/', views.delete, name='delete'),
    path('<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('<int:pk>/comment/', views.create_comment, name='create_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]
