from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('eula/', views.eula_page, name='eula'),
]
