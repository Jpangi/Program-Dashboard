
from . import views # Import views to connect routes to view functions
from django.urls import path, include
urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('programs/', views.programs, name='programs'),
    path('programs/create/', views.create_program, name='create_program'),
    path('upload/', views.upload_csv, name='upload_csv'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('programs/<int:pk>/update/', views.ProgramUpdate.as_view(), name='Program-update'),
    path('programs/<int:pk>/delete/', views.ProgramDelete.as_view(), name='Program-delete'),
]

