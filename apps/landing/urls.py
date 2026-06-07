from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.home, name='home'),
    path('pricing/', views.pricing, name='pricing'),
    path('features/', views.features, name='features'),

    # 购买页面城市数据 API
    path('api/municipality-city/', views.municipality_city, name='municipality_city'),
    path('api/not-municipality-city/', views.not_municipality_city, name='not_municipality_city'),
]
