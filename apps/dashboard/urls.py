from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('area_input', views.area_input, name='area_input'),
    path('indicator-check', views.indicator_check, name='indicator_check'),  


    # 城市数据查询路径
    path('get-city-map/', views.get_city_map, name='city_map_query'),
    path('get-area-map/', views.get_area_map, name='area_map_query'),
    
    path('single-indicator-year-query/', views.dashboard_single_query, name='single_query'),
    path('single-indicator-year-query-area/', views.dashboard_single_query_area, name='single_query_area'),
    path('order-price/', views.dashboard_order_price, name='order_price'),
    path('single-indicator-city-query/', views.dashboard_single_indicator_city_query, name='single_indicator_query'),
    path('many-indicator-query/', views.dashboard_many_indicator_query, name='many_indicator_query'),

    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('settings/generate-api-key/', views.generate_api_key, name='generate_api_key'),
    path('subscription/plans/', views.subscription_plans, name='subscription_plans'),
    path('subscription/plans/<slug:plan_slug>/subscribe/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/trial/', views.start_trial, name='start_trial'),

    path('submit/', views.submit_data, name='submit_data'),
    path('submit-area/', views.submit_area_data, name='submit_area_data'),

    path('single_indicator_query/', views.single_indicator_query, name='single_indicator_query'),
    path('single_indicator_area_query/', views.single_indicator_area_query, name='single_indicator_area_query'),
    path('single_indicator_city_query/', views.single_indicator_city_query, name='single_indicator_city_query'),
    path('many_indicator_city_query/', views.many_indicator_city_query, name='many_indicator_city_query'),
    
    path('upload_excel/', views.upload_excel, name='upload_excel'),
    path('upload_excel_area/', views.upload_excel_area, name='upload_excel_area'),

    # 核查指标API接口
    path('api/check-data/', views.check_data_api, name='check_data_api'),



    path('api/pricing-config/', views.get_pricing_config, name='get_pricing_config'),





] 