from django.urls import path
from . import views

app_name = 'messages_app'

urlpatterns = [
    path('', views.conversations_list, name='conversations'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
]
