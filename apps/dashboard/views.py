from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse  
import json
from apps.coredata.models.indicator import Indicator
from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS


import secrets
from .models import UserSettings, SubscriptionPlan

@login_required
@require_http_methods(['GET'])
def dashboard_home(request):
    return render(request, 'dashboard/home.html')

@login_required
@require_http_methods(['GET'])
def dashboard_single_query(request):
    return render(request, 'dashboard/single_query.html')


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('dashboard:profile')
    return render(request, 'dashboard/profile.html')

@login_required
@require_http_methods(['GET', 'POST'])
def settings(request):
    # Get or create user settings
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle notification settings
        user_settings.notify_comments = request.POST.get('comments') == 'on'
        user_settings.notify_updates = request.POST.get('updates') == 'on'
        user_settings.notify_marketing = request.POST.get('marketing') == 'on'
        user_settings.save()
        
        messages.success(request, 'Settings updated successfully.')
        return redirect('dashboard:settings')
    
    # Prepare context with current settings
    context = {
        'notification_settings': {
            'comments': user_settings.notify_comments,
            'updates': user_settings.notify_updates,
            'marketing': user_settings.notify_marketing,
        },
        'subscription': {
            'plan': user_settings.subscription_plan,
            'status': user_settings.subscription_status,
            'is_active': user_settings.is_subscription_active,
            'is_trial': user_settings.is_trial_active,
            'start_date': user_settings.subscription_start_date,
            'end_date': user_settings.subscription_end_date,
            'trial_end_date': user_settings.trial_end_date,
        },
        'api': {
            'has_key': bool(user_settings.api_key),
            'key_created_at': user_settings.api_key_created_at,
        }
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@require_http_methods(['POST'])
def generate_api_key(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    # Generate a new API key
    api_key = secrets.token_urlsafe(32)
    user_settings.api_key = api_key
    user_settings.api_key_created_at = timezone.now()
    user_settings.save()
    
    messages.success(request, 'API key generated successfully.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['GET'])
def subscription_plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    user_settings = UserSettings.objects.get(user=request.user)
    
    context = {
        'plans': plans,
        'current_plan': user_settings.subscription_plan,
        'subscription_status': user_settings.subscription_status,
        'is_subscription_active': user_settings.is_subscription_active,
        'is_trial_active': user_settings.is_trial_active,
    }
    return render(request, 'dashboard/subscription_plans.html', context)

@login_required
@require_http_methods(['POST'])
def subscribe_to_plan(request, plan_slug):
    plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
    user_settings = UserSettings.objects.get(user=request.user)
    
    # Check if user already has an active subscription
    if user_settings.is_subscription_active:
        messages.warning(request, 'You already have an active subscription.')
        return redirect('dashboard:subscription_plans')
    
    # Update user settings with new subscription
    user_settings.subscription_plan = plan
    user_settings.subscription_status = 'active'
    user_settings.subscription_start_date = timezone.now()
    
    # Set subscription end date based on interval
    if plan.interval == 'monthly':
        user_settings.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
    else:  # yearly
        user_settings.subscription_end_date = timezone.now() + timezone.timedelta(days=365)
    
    user_settings.save()
    
    messages.success(request, f'Successfully subscribed to {plan.name} plan.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['POST'])
def cancel_subscription(request):
    user_settings = UserSettings.objects.get(user=request.user)
    
    if not user_settings.is_subscription_active:
        messages.warning(request, 'You do not have an active subscription to cancel.')
        return redirect('dashboard:settings')
    
    user_settings.subscription_status = 'cancelled'
    user_settings.save()
    
    messages.success(request, 'Your subscription has been cancelled.')
    return redirect('dashboard:settings')

@login_required
@require_http_methods(['POST'])
def start_trial(request):
    user_settings = UserSettings.objects.get(user=request.user)
    
    if user_settings.is_subscription_active or user_settings.is_trial_active:
        messages.warning(request, 'You already have an active subscription or trial.')
        return redirect('dashboard:subscription_plans')
    
    # Start trial period (14 days)
    user_settings.subscription_status = 'trial'
    user_settings.trial_end_date = timezone.now() + timezone.timedelta(days=14)
    user_settings.save()
    
    messages.success(request, 'Trial period started successfully.')
    return redirect('dashboard:settings') 




@login_required
@require_http_methods(['POST'])
def submit_data(request):
    """处理表单提交"""
    try:
        # 获取表单数据
        rows_json = request.POST.get('rows_json', '[]')
        rows_data = json.loads(rows_json)
        
        print(f"=== 接收到的数据 ==  {rows_data}")
        print(f"数据条数: {len(rows_data)}")
        
        # 处理每一行数据
        for row in rows_data:
            city = row.get('city')
            groups = row.get('groups', [])
            
            print(f"\n城市: {city}")
            for i, group in enumerate(groups):
                print(f"  指标{i+1}:")
                print(f"    数值: {group.get('value')}")
                print(f"    备注: {group.get('note')}")
                print(f"    来源: {group.get('source')}")
                print(f"    参考: {group.get('reference')}")
        
        # 保存数据到数据库
        save_to_database(rows_data)
        # 返回成功响应
        return JsonResponse({
            'success': True,
            'message': f'成功提交 {len(rows_data)} 条记录',
            'count': len(rows_data)
        })
        
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'处理数据时出错: {str(e)}'
        }, status=500)
    

# === 数据保存函数 ===
def save_to_database(rows_data):
    """
    将 rows_data 批量保存到 Indicator 表。
    rows_data: [
        {
            'city': '城市ID',
            'province': '省ID',
            'year': 2026,
            'groups': [
                {
                    'indicator_key': 'gdp_per_capita',
                    'value': '123.45',
                    'note': '备注',
                    'source': 'CITY_STAT_YB',
                    'reference': '去年参考',
                },
                ...
            ]
        },
        ...
    ]
    """
    # 构建城市名到代码的映射
    city_name_to_code = {}
    for prov in CHINA_REGIONS:
        for city in prov.get('cities', []):
            city_name_to_code[city['name'].replace('市','')] = int(city['code'])
        # 直辖市本身也作为城市
        if prov['province_name'].endswith('市'):
            city_name_to_code[prov['province_name'].replace('市','')] = int(prov['province_code'])

    for row in rows_data:
        city_name = row.get('city')
        province_id = row.get('province')
        year = row.get('year') or None
        groups = row.get('groups', [])
        # 支持“北京市”/“北京”都能识别
        city_key = city_name.replace('市','') if city_name else ''
        city_id = city_name_to_code.get(city_key, 0)
        for group in groups:
            name_en = group.get('indicator_key')
            value = group.get('value')
            source = group.get('source')
            note = group.get('note')
            Indicator.objects.create(
                year=year,
                province_id=province_id or 0,
                city_id=city_id,
                source=source or '',
                value=value or 0,
                name_en=name_en or '',
                name_zh=note or '',  # 备注直接写入 name_zh
                input_form=Indicator.InputForm.INPUT,
                indicator_type=Indicator.IndicatorType.OTHER,
            )