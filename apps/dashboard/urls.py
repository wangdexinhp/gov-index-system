from django.urls import path
from . import views
from . import coverage_views
from . import indicator_audit_views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('area_input', views.area_input, name='area_input'),
    path('indicator-check', views.indicator_check, name='indicator_check'),  
    path('indicator-check-2', views.indicator_check_2, name='indicator_check_2'),  


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

    # 指标校验 API
    path('api/check-data/', indicator_audit_views.check_data_api, name='check_data_api'),
    path('api/indicator-audit-years/', indicator_audit_views.indicator_audit_years_api, name='indicator_audit_years'),
    path('api/indicator-audit-groups/', indicator_audit_views.indicator_audit_groups_api, name='indicator_audit_groups'),

    # 数据覆盖查询 API
    path('api/coverage-years/', coverage_views.coverage_years_api, name='coverage_years'),
    path('api/coverage-overview/', coverage_views.coverage_overview_api, name='coverage_overview'),
    path('api/missing-records/', coverage_views.missing_records_api, name='missing_records'),
    path('api/rebuild-coverage-stats/', coverage_views.rebuild_coverage_stats_api, name='rebuild_coverage_stats'),

    # 价格配置API接口
    path('api/pricing-config/', views.get_pricing_config, name='get_pricing_config'),
    path('api/update-pricing-config/', views.update_pricing_config, name='update_pricing_config'),

    # 指标配置API接口
    path('api/org-indicator-config/', views.org_indicator_config, name='org_indicator_config'),
    path('api/personal-indicator-config/', views.personal_indicator_config, name='personal_indicator_config'),

    # 会员激活接口
    path('api/activate-membership/', views.activate_membership, name='activate_membership'),


]
