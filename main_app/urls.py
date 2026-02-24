from django.urls import path
from . import views # Import views to connect routes to view functions

urlpatterns = [
    path('', views.home, name='home'),
    path('programs/create/', views.create_program, name='create_program'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
]

