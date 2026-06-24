from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import IntegrityError

from django.utils import timezone
from django.http import JsonResponse, HttpResponse  
import json,re
from apps.coredata.models.indicator import Indicator
from apps.coredata.models.indicator import IndicatorArea
from apps.coredata.models.price import PricingConfig, IndicatorConfig, DurationMultiplierConfig

from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS,html_city_Map,html_area_Map
    
from apps.coredata.management.commands.indicator_zh_en import INDIMAP,INDIMAP_UNIT,AREA_INDIMAP,AREA_INDIMAP_UNIT
from apps.coredata.utils.mapper import get_city_name_to_code, get_province_name_to_code,get_city_code_to_province

from apps.coredata.excel_color_sources import DEFAULT_EXCEL_SOURCE
from apps.coredata.indicator_input_methods import IndicatorInputMethod, normalize_data_source
from apps.coredata.services.excel_upload_service import (
    extract_cell_fields,
    has_excel_cell_value,
    parse_area_indicator_excel,
    parse_city_indicator_excel,
)

import secrets
from functools import wraps
from .models import UserSettings, SubscriptionPlan


# ==================== 管理员权限验证装饰器 ====================
def login_required_json(view_func):
    """未登录时返回 JSON，避免购买 API 被重定向到登录页。"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "请先登录后再操作"}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """仅管理员或超级用户可访问。"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if request.user.is_superuser or (profile and profile.membership_level == "admin"):
            return view_func(request, *args, **kwargs)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
            return JsonResponse({"success": False, "message": "需要管理员权限"}, status=403)
        return redirect("/")
    return _wrapped_view


# ==================== 会员权限验证装饰器 ====================
def check_membership(view_func):
    """
    会员权限验证装饰器
    验证用户是否有权限查看请求的城市和指标数据
    从 GET 参数中提取 city 和 name_zh 进行校验
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        profile = request.user.profile
        
        # 管理员可以查看所有数据
        if profile.membership_level == 'admin':
            return view_func(request, *args, **kwargs)
        
        # 检查会员是否过期
        if not profile.is_membership_active:
            return JsonResponse({
                'success': False,
                'message': '您的会员已过期，请续费后继续使用',
                'code': 'membership_expired'
            }, status=403)
        
        # 解析会员权限范围
        import json as _json
        try:
            allowed_cities = _json.loads(profile.membership_scope_city or '[]')
            allowed_indicators = _json.loads(profile.membership_scope_item or '[]')
        except (json.JSONDecodeError, TypeError):
            allowed_cities = []
            allowed_indicators = []
        
        # 从 GET 参数中提取请求的城市
        requested_cities = []
        city_param = request.GET.get('city', '')
        if city_param:
            requested_cities = [c.strip() for c in city_param.split(',') if c.strip()]
        
        # 从 GET 参数中提取请求的指标
        requested_indicators = []
        indicator_param = request.GET.get('name_zh', '')
        if indicator_param:
            requested_indicators = [ind.strip() for ind in indicator_param.split(',') if ind.strip()]
        
        # 检查城市权限
        if requested_cities:
            from apps.coredata.services.scope_service import is_city_allowed
            if '全国' not in allowed_cities:
                unauthorized_cities = [c for c in requested_cities if not is_city_allowed(c, allowed_cities)]
                if unauthorized_cities:
                    return JsonResponse({
                        'success': False,
                        'message': f'您没有以下城市的查看权限: {", ".join(unauthorized_cities)}',
                        'code': 'city_not_allowed',
                        'unauthorized_cities': unauthorized_cities,
                        'allowed_cities': allowed_cities,
                    }, status=403)
        
        # 检查指标权限
        if requested_indicators:
            unauthorized_indicators = [ind for ind in requested_indicators if ind not in allowed_indicators]
            if unauthorized_indicators:
                return JsonResponse({
                    'success': False,
                    'message': f'您没有以下指标的查看权限: {", ".join(unauthorized_indicators)}',
                    'code': 'indicator_not_allowed',
                    'unauthorized_indicators': unauthorized_indicators,
                    'allowed_indicators': allowed_indicators,
                }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


@login_required
@require_http_methods(['GET'])
def dashboard_home(request):
    print(f"用户 {request.user.profile.membership_level} 访问了仪表盘首页")
    if request.user.profile.membership_level != 'admin':
        return redirect('/') 
    return render(request, 'dashboard/home.html')

@login_required
@require_http_methods(['GET'])
def area_input(request):
    print(f"用户 {request.user.profile.membership_level} 访问了区域输入页面")
    if request.user.profile.membership_level != 'admin':
        return redirect('/') 
    return render(request, 'dashboard/input_area.html')

@login_required
@login_required
@require_http_methods(['GET'])
def indicator_check(request):
    return render(request, 'dashboard/indic_data_check.html')


@login_required
@require_http_methods(['GET'])
def indicator_check_2(request):
    return render(request, 'dashboard/indic_data_check_cover.html')



@login_required
@require_http_methods(['GET'])
def dashboard_single_query(request):
    return render(request, 'dashboard/single_query.html')

@login_required
@require_http_methods(['GET'])
def dashboard_single_query_area(request):
    return render(request, 'dashboard/single_query_area.html')

@admin_required
@require_http_methods(['GET'])
def dashboard_order_price(request):
    return render(request, 'dashboard/order_price.html')



# @login_required
# @require_http_methods(['GET'])
# def dashboard_single_indicator_city_query(request):
#     return render(request, 'dashboard/single_indicator_city_query.html')

@login_required
@require_http_methods(['GET'])
def dashboard_single_indicator_city_query(request):
    return render(request, 'dashboard/single_indicator_city_query.html')



@login_required
@require_http_methods(['GET'])
def dashboard_many_indicator_query(request):
    return render(request, 'dashboard/many_indic_query.html')


@login_required
@require_http_methods(['GET', 'POST'])
def get_city_map(request):
    return JsonResponse(html_city_Map, safe=False)


@login_required
@require_http_methods(['GET', 'POST'])
def get_area_map(request):
    city_name = request.GET.get('city') or request.POST.get('city') or ''
    city_name = city_name.strip()
    if not city_name:
        return JsonResponse([], safe=False)

    areas = html_area_Map.get(city_name)
    if areas is None:
        if city_name.endswith('市'):
            areas = html_area_Map.get(city_name.replace('市', ''))
        else:
            areas = html_area_Map.get(f"{city_name}市")

    return JsonResponse(areas or [], safe=False)




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
@user_passes_test(lambda u: u.is_superuser)  
@require_http_methods(['POST'])
def submit_data(request):
    """处理表单提交"""
    try:
        # 获取表单数据
        print("=== 接收到的POST数据 ===",request.POST.dict())
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
    for row in rows_data:
        city_name = row.get('city')
        province_name = row.get('province')
        year = row.get('year') or None
        groups = row.get('groups', [])
        # 支持“北京市”/“北京”都能识别
        city_key = city_name.replace('市','') if city_name else ''
        city_name_to_code = get_city_name_to_code()
        province_name_to_code = get_province_name_to_code()
        city_id = city_name_to_code.get(city_key, 0)
        prov_key = province_name.replace('市','') if province_name else ''
        province_id = province_name_to_code.get(prov_key, 0)
        for group in groups:
            value = group.get('value')
            note = group.get('note')
            name_zh = group.get('name_zh')
            name_zh = re.sub(r'\([^)]*\)$', '', name_zh)
            name_en = group.get('name_en') or INDIMAP.get(name_zh)

            source = normalize_data_source(group.get('source'))
            input_method = group.get('input_method') or IndicatorInputMethod.MANUAL

            Indicator.objects.update_or_create(
                year=year,
                city_id=city_id,
                name_en=name_en or '',
                defaults={
                    'province_id': province_id,
                    'source': source or '',
                    'input_method': input_method,
                    'value': value or 0,
                    'note': note or '',
                    'name_zh': name_zh or '',
                    'input_form': Indicator.InputForm.INPUT,
                    'indicator_type': Indicator.IndicatorType.OTHER,
                },
            )

def save_area_to_database(rows_data):
    """
    将 rows_data 批量保存到 IndicatorArea 表。
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
    for row in rows_data:
        city_name = row.get('city')
        area=row.get('area')
        province_name = row.get('province')
        year = row.get('year') or None
        groups = row.get('groups', [])
        # 支持“北京市”/“北京”都能识别
        city_key = city_name.replace('市','') if city_name else ''
        city_name_to_code = get_city_name_to_code()
        province_name_to_code = get_province_name_to_code()
        city_id = city_name_to_code.get(city_key, 0)
        prov_key = province_name.replace('市','') if province_name else ''
        province_id = province_name_to_code.get(prov_key, 0)
        for group in groups:
            value = group.get('value')
            note = group.get('note')
            name_zh = group.get('name_zh')
            name_zh = re.sub(r'\([^)]*\)$', '', name_zh)
            name_en = INDIMAP.get(name_zh)

            source = normalize_data_source(group.get('source'))
            input_method = group.get('input_method') or IndicatorInputMethod.MANUAL

            IndicatorArea.objects.create(
                year=year,
                province_id=province_id,
                city_id=city_id,
                area=area,
                source=source or '',
                input_method=input_method,
                value=value or 0,
                name_en=name_en or '',
                note=note or '',
                name_zh= name_zh or '',  
                input_form=IndicatorArea.InputForm.INPUT,
                indicator_type=IndicatorArea.IndicatorType.OTHER,
            )


# 区县数据提交接口
@login_required
@require_http_methods(['POST'])
def submit_area_data(request):
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
        save_area_to_database(rows_data)
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
    





# === 单一指标历年查询接口 ===
@check_membership
@require_http_methods(['GET'])
def single_indicator_query(request):
    # indicator_en = request.GET.get('name_en')
    # print("indicator_en=",indicator_en)
    indicator_zh = request.GET.get('name_zh')
    indicator_en = INDIMAP.get(indicator_zh)
    start_year = request.GET.get('start_year')
    end_year = request.GET.get('end_year')
    city_name = request.GET.get('city')
    province_name = request.GET.get('province')
    unit = INDIMAP_UNIT.get(indicator_en, "").get('unit', "")
    if unit is None:
        unit = ""
    # 构建城市名到代码、以及省份名到代码的映射
    city_name_to_code = {}
    province_name_to_code = {}
    for prov in CHINA_REGIONS:
        pname = prov['province_name']
        pcode = int(prov['province_code'])
        province_name_to_code[pname] = pcode
        if pname.endswith('市'):
            province_name_to_code[pname.replace('市','')] = pcode
        for city in prov.get('cities', []):
            city_name_to_code[city['name'].replace('市','')] = int(city['code'])

    city_id = None
    if city_name:
        city_key = city_name.replace('市','')
        city_id = city_name_to_code.get(city_key)
    province_id = None
    if province_name:
        prov_key = province_name.replace('市','')
        province_id = province_name_to_code.get(prov_key)

    # 构建查询条件
    filters = {}
    if indicator_en:
        filters['name_en'] = indicator_en
    # if indicator_zh:
    #     filters['name_zh'] = indicator_zh
    if start_year:
        filters['year__gte'] = start_year
    if end_year:
        filters['year__lte'] = end_year
    if city_id:
        filters['city_id'] = city_id
    if province_id:
        filters['province_id'] = province_id

    indicators = Indicator.objects.filter(**filters).order_by('year')
    data = []
    for ind in indicators:
        data.append({
            'year': ind.year,
            'value': ind.value,
            'note': ind.note,
            'source': ind.source,
            'unit' : unit,
        })
    return JsonResponse({
        'success': True,
        'data': data
    })


# === 区县单一指标历年查询接口 ===
@check_membership
@require_http_methods(['GET'])
def single_indicator_area_query(request):
    indicator_zh = request.GET.get('name_zh')
    indicator_en = AREA_INDIMAP.get(indicator_zh) or INDIMAP.get(indicator_zh)
    start_year = request.GET.get('start_year')
    end_year = request.GET.get('end_year')
    city_name = request.GET.get('city')
    province_name = request.GET.get('province')
    area = (request.GET.get('area') or '').strip()

    unit = AREA_INDIMAP_UNIT.get(indicator_en, {}).get('unit', '') if indicator_en else ''
    if not unit:
        unit = INDIMAP_UNIT.get(indicator_en, {}).get('unit', '') if indicator_en else ''
    if unit is None:
        unit = ""

    city_name_to_code = {}
    province_name_to_code = {}
    for prov in CHINA_REGIONS:
        pname = prov['province_name']
        pcode = int(prov['province_code'])
        province_name_to_code[pname] = pcode
        if pname.endswith('市'):
            province_name_to_code[pname.replace('市', '')] = pcode
        for city in prov.get('cities', []):
            city_name_to_code[city['name'].replace('市', '')] = int(city['code'])

    city_id = None
    if city_name:
        city_key = city_name.replace('市', '')
        city_id = city_name_to_code.get(city_key)

    province_id = None
    if province_name:
        prov_key = province_name.replace('市', '')
        province_id = province_name_to_code.get(prov_key)

    filters = {}
    if indicator_en:
        filters['name_en'] = indicator_en
    if start_year:
        filters['year__gte'] = start_year
    if end_year:
        filters['year__lte'] = end_year
    if city_id:
        filters['city_id'] = city_id
    if province_id:
        filters['province_id'] = province_id
    if area:
        filters['area'] = area

    indicators = IndicatorArea.objects.filter(**filters).order_by('year')
    data = []
    for ind in indicators:
        data.append({
            'year': ind.year,
            'area': ind.area,
            'value': ind.value,
            'note': ind.note,
            'source': ind.source,
            'unit': unit,
        })

    return JsonResponse({
        'success': True,
        'data': data
    })

# === 单一指标多城市查询接口 ===
@check_membership
@require_http_methods(['GET'])
def single_indicator_city_query(request):
    indicator_zh = request.GET.get('name_zh')
    indicator_en = INDIMAP.get(indicator_zh)
    start_year = request.GET.get('start_year')
    end_year = request.GET.get('end_year')
    citys_param = request.GET.get('city')
    print("citys=",citys_param)
    unit = INDIMAP_UNIT.get(indicator_en, "").get('unit', "")
    if unit is None:
        unit = ""
    # 构建城市名到代码、以及省份名到代码的映射
    city_name_to_code = {}
    for prov in CHINA_REGIONS:
        for city in prov.get('cities', []):
            city_name_to_code[city['name'].replace('市','')] = int(city['code'])

    city_ids= []
    if citys_param:
        city_names = [name.strip() for name in citys_param.split(',') if name.strip()]        
        for city_name in city_names:
            city_key = city_name.replace('市', '')
            city_id = city_name_to_code.get(city_key)
            if city_id:
                city_ids.append(city_id)

    # 构建查询条件
    filters = {}
    if indicator_en:
        filters['name_en'] = indicator_en
    if indicator_zh:
        filters['name_zh'] = indicator_zh
    if start_year:
        filters['year__gte'] = start_year
    if end_year:
        filters['year__lte'] = end_year

    # 查询数据
    if city_ids:
        # 使用 __in 查询多个城市
        indicators = Indicator.objects.filter(
            **filters,
            city_id__in=city_ids
        ).order_by('city_id', 'year')
    else:
        indicators = Indicator.objects.filter(**filters).order_by('year')

    # 按城市组织数据
    result_data = {}
    for ind in indicators:
        city_code = ind.city_id
        city_name = get_city_name_by_code(city_code)  # 需要实现这个函数
        
        if city_name not in result_data:
            result_data[city_name] = []
        
        result_data[city_name].append({
            'year': ind.year,
            'value': ind.value,
            'note': ind.note,
            'source': ind.source,
            'unit': unit,
        })
    
    return JsonResponse({
        'success': True,
        'data': result_data
    })

def get_city_name_by_code(city_code):
    """根据城市代码获取城市名"""
    for prov in CHINA_REGIONS:
        for city in prov.get('cities', []):
            if int(city['code']) == city_code:
                return city['name']
    return f"未知城市({city_code})"


# === 指标数据核对查询API ===



# 城市上传文件
@login_required
@require_http_methods(['POST'])
def upload_excel(request):
    """处理Excel文件上传，按单元格底色识别数据来源。"""
    year = request.POST.get('year')
    excel_file = request.FILES.get('excel_file')
    if not excel_file:
        return JsonResponse({
            'success': False,
            'message': '未上传文件'
        }, status=400)

    try:
        rows_data = parse_city_indicator_excel(excel_file)
        if not rows_data:
            return JsonResponse({
                'success': False,
                'message': 'Excel 无有效数据行'
            }, status=400)
        save_df_to_database(rows_data=rows_data, year=year)
        return JsonResponse({
            'success': True,
            'message': '成功处理Excel文件（已按底色识别来源）'
        })
    except Exception as e:
        print(f"处理Excel文件时出错: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'处理Excel文件时出错: {str(e)}'
        }, status=500)

# 区县上传文件接口
@login_required
@require_http_methods(['POST'])
def upload_excel_area(request):
    """区县处理Excel文件上传，按单元格底色识别数据来源。"""
    year = request.POST.get('year')
    excel_file = request.FILES.get('excel_file')
    if not excel_file:
        return JsonResponse({
            'success': False,
            'message': '未上传文件'
        }, status=400)

    try:
        rows_data = parse_area_indicator_excel(excel_file)
        if not rows_data:
            return JsonResponse({
                'success': False,
                'message': 'Excel 无有效数据行'
            }, status=400)

        city_col = next((c for c in rows_data[0] if c in ['城市', '城市名称', '地市']), None)
        if not city_col:
            city_col = next((c for c in rows_data[0] if '城市' in str(c)), None)

        area_col = next((c for c in rows_data[0] if c in [
            '所辖区县名称', '所辖区域名称', '区县', '区县名称', '区县名', '区域名称'
        ]), None)
        if not area_col:
            area_col = next((c for c in rows_data[0] if ('区县' in str(c) or '区域' in str(c))), None)

        if not city_col or not area_col:
            return JsonResponse({
                'success': False,
                'message': 'Excel缺少“城市/城市名称”或“所辖区域名称/所辖区县名称/区县”列'
            }, status=400)

        normalized_rows = []
        last_city = ''
        for row in rows_data:
            city_val, _, _ = extract_cell_fields(row.get(city_col))
            city_name = str(city_val).strip() if city_val is not None else ''
            if city_name:
                last_city = city_name
            else:
                city_name = last_city

            area_val, _, _ = extract_cell_fields(row.get(area_col))
            area_name = str(area_val).strip() if area_val is not None else ''
            if not city_name or not area_name or city_name in ('nan', 'None') or area_name in ('nan', 'None'):
                continue

            normalized = dict(row)
            normalized['城市'] = city_name
            normalized['area'] = area_name
            normalized_rows.append(normalized)

        if not normalized_rows:
            return JsonResponse({
                'success': False,
                'message': 'Excel 无有效城市/区县数据行'
            }, status=400)

        save_area_df_to_database(rows_data=normalized_rows, year=year)
        return JsonResponse({
            'success': True,
            'message': '成功处理Excel文件（已按底色识别来源）'
        })
    except Exception as e:
        print(f"处理区县Excel文件时出错: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'处理Excel文件时出错: {str(e)}'
        }, status=500)



# === 数据保存函数 ===
def save_df_to_database(rows_data, year):
    print(f"=== 准备保存的数据 ===\n{rows_data[:2]}")  # 打印前两行数据预览
    # 构建城市名到代码、以及省份名到代码的映射
    # rows_data =  [{'A': '京', '城市': '北京', '所辖市区县个数_市': 0, '区': 14, '县': 2, '城镇户籍人口': 1089.8, '农业人口': 243.6, '年末实有企业数_个体工商户': 653319, '内资企业': 39533, '外资企业': 1657, '私营企业': 838099, '高新技术企业_产值': 'A', '增加值': 'A', '采矿（掘)业就业人员人数': 6.2, '制造业就业人员人数': 129.9, '采矿（掘)业在岗职工人数': 6.09, '制造业在岗职工人数': 97.43, '财政总支出': 4524.67, '一般预算支出_一般公共服务支出': 272.23, '公共安全支出': 'A', '文化体育传媒支出': 163.9, '环保支出': 213.36, '园林绿地面积': 77129, '专利授权量': 74661, '城镇单位职工工资总额': 72933000.0, '社会从业\n人员': 1156.7, '机关单位_工资总额': 'A', '就业人数': 'A', '公共管理和社会组织工资总额': 3434882, '公共管理和社会组织在岗职工人数': 424414, '取缔无照经营个数': 91, '查处取缔无照经营个数': 2037, '参保人数_城镇养老保险参保人数': 1392.6, '城镇医疗保险参保人数': 1604.25, '农村养老保险参保人数': 173.4, '户数统计_总户数': 522.6, '有线电视用户数': 551.57, '互联网用户数': 553, '刑事案件立案件数': 153334, '刑事案件破案件数': 91.7826608669567, '二氧化硫排放总量_2012年': 40347, 'R&D经费数': 1268.8, 'R&D经费与GDP之比': 5.95, '自来水受益村数': 'A', '村委会个数': 3937, '受理信访举报案件数': 1424, '文化馆': 19, '博物馆': 171, '群众艺术馆': 1, '文化艺术团体': 'A', '体育馆': 70, '城镇最低生活保障人数': 89135, '农村最低生活保障人数': 51324, '贪污贿赂人数': 429, '渎职侵权人数': 78, '财政总收入': 7214.5, '财政总收入增长率': 29.6, '固定资产投资总额增长率': 7.5, '全社会消费品零售总额增长率': 8.6, '进出口总额增长率': -3.4, '实际利用外资金额增长率': 6.07, '规模以上工业企业增加值': 3612, '规模以上工业企业产值增加值增长率': 6.2, '国有资产保值增值率': 105.52, '万元GDP综合能源消耗': 0.36, '万元GDP综合能源消耗降低率': 5.29, '城镇化率': 86.4, '城镇家庭居民人均可支配收入增长率': 7.2, '农村家庭居民人均纯收入增长率': 8.6, '居民消费价格指数CPI': 101.6, '工业品出厂价格指数PPI': 99.1, '亿元GDP生产安全事故死亡率': 0.051, '十万人工矿商贸从业人员事故死亡率': 0.94, '食品质量抽样检测合格率': 97.46, '药品安全抽样合格率': 99.88, '工业产品质量抽样合格率': 'A', '查处农资违法案件的数量': 25, '查办各类经济违法案件的数量': 'A', '查办违法广告的件数': 860, '查办商标侵权案件的件数': 472, '消费者维权案件办理率': 100, '出生人口性别比': 'A', '人口出生率': 9.75, '符合政策生育率': 'A', '年末实有社会组织登记数量': 9083, '万人刑事案件发案件数': 114.994750262487, '调处各类矛盾纠纷件数': 194100, '成功调处各类矛盾纠纷数': 188600, '受理各类法律援助案件的数量': 18273, '火灾死亡人数': 51, '接待群众来信来访人次': 39149, '城镇新增就业人数': 42.65, '农村养老保险覆盖率': 71.1822660098522, '新建各类保障性住房面积': 509.5, '农村自来水覆盖率（农村安全饮水覆盖率）': 99.55, '人均拥有道路面积': 7.93, '每万人拥有公交汽车数量': 18.76, '有线电视入户率': 106.85, '高中阶段毛入学率': 'A', '新农合参合率': 'A', '森林覆盖率': 35.84, '水土流失治理面积': 40000, '工业废水排放达标率': 'A', '工业固体废弃物综合利用率': 87.67, '生活垃圾无害化处理率': 99.6, '城镇生活污水处理率': 86.1, '城市空气质量指数': 46.027397260274, '城市区域环境噪音指数（市区区域环境噪音平均等效声级值）': 53.6, '违法违纪发案件数': 'A', '行政复议案件办结率': 'A', '行政复议案件申请量': 1840, '受理行政诉讼的案件数量': 1840, '被依法追究责任的领导干部个数': 'A', '主动公开政府信息件数_2011年': 181600, '2012年': 225800, '主动公开政府信息增长率': 24.3392070484581, '依申请公开政府信息件数_2013年': 16888, '2014年': 34766, '依申请公开政府信息增长率': 105.862150639507, '因公开问题申请行政复议的数量': 1840}, {'A': '津', '城市': '天津', '所辖市区县个数_市': 0, '区': 13, '县': 3, '城镇户籍人口': 645.05, '农业人口': 371.61, '年末实有企业数_个体工商户': 366, '内资企业': 264994, '外资企业': 11498, '私营企业': 552700, '高新技术企业_产值': 8467.12, '增加值': 331.1, '采矿（掘)业就业人员人数': 6.64, '制造业就业人员人数': 118.99, '采矿（掘)业在岗职工人数': 0.46, '制造业在岗职工人数': 6.52, '财政总支出': 2884.7, '一般预算支出_一般公共服务支出': 158.08, '公共安全支出': 139.31, '文化体育传媒支出': 47.87, '环保支出': 57.93, '园林绿地面积': 25307, '专利授权量': 26351, '城镇单位职工工资总额': 20631400.0, '社会从业\n人员': 877.21, '机关单位_工资总额': 1189400, '就业人数': 139800, '公共管理和社会组织工资总额': 1301800, '公共管理和社会组织在岗职工人数': 144000, '取缔无照经营个数': 6007, '查处取缔无照经营个数': 2126, '参保人数_城镇养老保险参保人数': 657.28, '城镇医疗保险参保人数': 1023.62, '农村养老保险参保人数': 100.5, '户数统计_总户数': 362.63, '有线电视用户数': 313, '互联网用户数': 1014, '刑事案件立案件数': 'A', '刑事案件破案件数': 35.0205575118525, '二氧化硫排放总量_2012年': 195395, 'R&D经费数': 464.69, 'R&D经费与GDP之比': 3, '自来水受益村数': 'A', '村委会个数': 3698, '受理信访举报案件数': 7231, '文化馆': 19, '博物馆': 22, '群众艺术馆': 19, '文化艺术团体': 51, '体育馆': 'A', '城镇最低生活保障人数': 135760, '农村最低生活保障人数': 101447, '贪污贿赂人数': 341, '渎职侵权人数': 56, '财政总收入': 2390.02, '财政总收入增长率': 15.0, '固定资产投资总额增长率': 15.1, '全社会消费品零售总额增长率': 6.0, '进出口总额增长率': 4.2, '实际利用外资金额增长率': 12.1, '规模以上工业企业增加值': 1520.52, '规模以上工业企业产值增加值增长率': 10.1, '国有资产保值增值率': 101.6, '万元GDP综合能源消耗': 0.54, '万元GDP综合能源消耗降低率': 6.0, '城镇化率': 82.3, '城镇家庭居民人均可支配收入增长率': 8.7, '农村家庭居民人均纯收入增长率': 10.8, '居民消费价格指数CPI': 101.9, '工业品出厂价格指数PPI': 96.3, '亿元GDP生产安全事故死亡率': 0.0232721834458473, '十万人工矿商贸从业人员事故死亡率': 'A', '食品质量抽样检测合格率': 98.38, '药品安全抽样合格率': 'A', '工业产品质量抽样合格率': 97.85, '查处农资违法案件的数量': 'A', '查办各类经济违法案件的数量': 250, '查办违法广告的件数': 351, '查办商标侵权案件的件数': 396, '消费者维权案件办理率': 99.64, '出生人口性别比': 'A', '人口出生率': 8.19, '符合政策生育率': 98.45, '年末实有社会组织登记数量': 4729, '万人刑事案件发案件数': nan, '调处各类矛盾纠纷件数': 90028, '成功调处各类矛盾纠纷数': 88230, '受理各类法律援助案件的数量': 4114, '火灾死亡人数': 'A', '接待群众来信来访人次': 13195, '城镇新增就业人数': 48.8, '农村养老保险覆盖率': 27.0444821183499, '新建各类保障性住房面积': '6.1万套', '农村自来水覆盖率（农村安全饮水覆盖率）': 98.98, '人均拥有道路面积': 15.78, '每万人拥有公交汽车数量': 13.41, '有线电视入户率': 88.95, '高中阶段毛入学率': 100, '新农合参合率': 'A', '森林覆盖率': 9.87, '水土流失治理面积': 6400, '工业废水排放达标率': 'A', '工业固体废弃物综合利用率': 98.91, '生活垃圾无害化处理率': 96.23, '城镇生活污水处理率': 100, '城市空气质量指数': 47.9, '城市区域环境噪音指数（市区区域环境噪音平均等效声级值）': 53.6, '违法违纪发案件数': 670, '行政复议案件办结率': 'A', '行政复议案件申请量': 194, '受理行政诉讼的案件数量': 194, '被依法追究责任的领导干部个数': 'A', '主动公开政府信息件数_2011年': 123888, '2012年': 214499, '主动公开政府信息增长率': 73.1394485341599, '依申请公开政府信息件数_2013年': 5146, '2014年': 11399, '依申请公开政府信息增长率': 121.511853867081, '因公开问题申请行政复议的数量': 1074}]
    for row in rows_data:
        city_name = row.get('城市')
        city_name_to_code = get_city_name_to_code()
        city_id = city_name_to_code.get(city_name.replace('市',''), 0) if city_name else 0
        city_code_to_province = get_city_code_to_province()
        province_info = city_code_to_province.get(city_id)
        province_id = province_info['province_code'] if province_info else 0
        for col_name, raw_value in row.items():
            if col_name in ['城市', 'A']:
                continue
            value, source, note = extract_cell_fields(raw_value)
            if not has_excel_cell_value(value):
                continue
            name_zh = col_name
            source = normalize_data_source(source) or source or DEFAULT_EXCEL_SOURCE
            print(f"处理指标: {name_zh}，值: {value}，来源: {source}")
            name_en = INDIMAP.get(name_zh)
            if not name_en:
                print(f"未找到指标英文名映射，跳过: {name_zh}")
                continue
            try:
                Indicator.objects.create(
                    year=year,
                    province_id=province_id,
                    city_id=city_id,
                    source=source,
                    input_method=Indicator.InputMethod.EXCEL,
                    value=value,
                    name_en=name_en or '',
                    note=note or '',
                    name_zh=name_zh or '',
                    input_form=Indicator.InputForm.INPUT,
                    indicator_type=Indicator.IndicatorType.OTHER,
                )
            except IntegrityError as e:
                if 'Duplicate entry' in str(e):
                    print(f"跳过重复记录: {year}-{city_id}-{name_en}")
                    continue
                else:
                    print(f"保存指标时出错: {name_zh}, 错误: {e}")
                    continue
                    
            except Exception as e:
                print(f"保存指标时发生未知错误: {name_zh}, 错误: {e}")
                continue

# === 数据保存函数 ===
def save_area_df_to_database(rows_data, year):
    print(f"=== 准备保存的数据 ===\n{rows_data[:2]}")  # 打印前两行数据预览
    # 构建城市名到代码、以及省份名到代码的映射
    # rows_data =  [{'A': '京', '城市': '北京', '所辖市区县个数_市': 0, '区': 14, '县': 2, '城镇户籍人口': 1089.8, '农业人口': 243.6, '年末实有企业数_个体工商户': 653319, '内资企业': 39533, '外资企业': 1657, '私营企业': 838099, '高新技术企业_产值': 'A', '增加值': 'A', '采矿（掘)业就业人员人数': 6.2, '制造业就业人员人数': 129.9, '采矿（掘)业在岗职工人数': 6.09, '制造业在岗职工人数': 97.43, '财政总支出': 4524.67, '一般预算支出_一般公共服务支出': 272.23, '公共安全支出': 'A', '文化体育传媒支出': 163.9, '环保支出': 213.36, '园林绿地面积': 77129, '专利授权量': 74661, '城镇单位职工工资总额': 72933000.0, '社会从业\n人员': 1156.7, '机关单位_工资总额': 'A', '就业人数': 'A', '公共管理和社会组织工资总额': 3434882, '公共管理和社会组织在岗职工人数': 424414, '取缔无照经营个数': 91, '查处取缔无照经营个数': 2037, '参保人数_城镇养老保险参保人数': 1392.6, '城镇医疗保险参保人数': 1604.25, '农村养老保险参保人数': 173.4, '户数统计_总户数': 522.6, '有线电视用户数': 551.57, '互联网用户数': 553, '刑事案件立案件数': 153334, '刑事案件破案件数': 91.7826608669567, '二氧化硫排放总量_2012年': 40347, 'R&D经费数': 1268.8, 'R&D经费与GDP之比': 5.95, '自来水受益村数': 'A', '村委会个数': 3937, '受理信访举报案件数': 1424, '文化馆': 19, '博物馆': 171, '群众艺术馆': 1, '文化艺术团体': 'A', '体育馆': 70, '城镇最低生活保障人数': 89135, '农村最低生活保障人数': 51324, '贪污贿赂人数': 429, '渎职侵权人数': 78, '财政总收入': 7214.5, '财政总收入增长率': 29.6, '固定资产投资总额增长率': 7.5, '全社会消费品零售总额增长率': 8.6, '进出口总额增长率': -3.4, '实际利用外资金额增长率': 6.07, '规模以上工业企业增加值': 3612, '规模以上工业企业产值增加值增长率': 6.2, '国有资产保值增值率': 105.52, '万元GDP综合能源消耗': 0.36, '万元GDP综合能源消耗降低率': 5.29, '城镇化率': 86.4, '城镇家庭居民人均可支配收入增长率': 7.2, '农村家庭居民人均纯收入增长率': 8.6, '居民消费价格指数CPI': 101.6, '工业品出厂价格指数PPI': 99.1, '亿元GDP生产安全事故死亡率': 0.051, '十万人工矿商贸从业人员事故死亡率': 0.94, '食品质量抽样检测合格率': 97.46, '药品安全抽样合格率': 99.88, '工业产品质量抽样合格率': 'A', '查处农资违法案件的数量': 25, '查办各类经济违法案件的数量': 'A', '查办违法广告的件数': 860, '查办商标侵权案件的件数': 472, '消费者维权案件办理率': 100, '出生人口性别比': 'A', '人口出生率': 9.75, '符合政策生育率': 'A', '年末实有社会组织登记数量': 9083, '万人刑事案件发案件数': 114.994750262487, '调处各类矛盾纠纷件数': 194100, '成功调处各类矛盾纠纷数': 188600, '受理各类法律援助案件的数量': 18273, '火灾死亡人数': 51, '接待群众来信来访人次': 39149, '城镇新增就业人数': 42.65, '农村养老保险覆盖率': 71.1822660098522, '新建各类保障性住房面积': 509.5, '农村自来水覆盖率（农村安全饮水覆盖率）': 99.55, '人均拥有道路面积': 7.93, '每万人拥有公交汽车数量': 18.76, '有线电视入户率': 106.85, '高中阶段毛入学率': 'A', '新农合参合率': 'A', '森林覆盖率': 35.84, '水土流失治理面积': 40000, '工业废水排放达标率': 'A', '工业固体废弃物综合利用率': 87.67, '生活垃圾无害化处理率': 99.6, '城镇生活污水处理率': 86.1, '城市空气质量指数': 46.027397260274, '城市区域环境噪音指数（市区区域环境噪音平均等效声级值）': 53.6, '违法违纪发案件数': 'A', '行政复议案件办结率': 'A', '行政复议案件申请量': 1840, '受理行政诉讼的案件数量': 1840, '被依法追究责任的领导干部个数': 'A', '主动公开政府信息件数_2011年': 181600, '2012年': 225800, '主动公开政府信息增长率': 24.3392070484581, '依申请公开政府信息件数_2013年': 16888, '2014年': 34766, '依申请公开政府信息增长率': 105.862150639507, '因公开问题申请行政复议的数量': 1840}, {'A': '津', '城市': '天津', '所辖市区县个数_市': 0, '区': 13, '县': 3, '城镇户籍人口': 645.05, '农业人口': 371.61, '年末实有企业数_个体工商户': 366, '内资企业': 264994, '外资企业': 11498, '私营企业': 552700, '高新技术企业_产值': 8467.12, '增加值': 331.1, '采矿（掘)业就业人员人数': 6.64, '制造业就业人员人数': 118.99, '采矿（掘)业在岗职工人数': 0.46, '制造业在岗职工人数': 6.52, '财政总支出': 2884.7, '一般预算支出_一般公共服务支出': 158.08, '公共安全支出': 139.31, '文化体育传媒支出': 47.87, '环保支出': 57.93, '园林绿地面积': 25307, '专利授权量': 26351, '城镇单位职工工资总额': 20631400.0, '社会从业\n人员': 877.21, '机关单位_工资总额': 1189400, '就业人数': 139800, '公共管理和社会组织工资总额': 1301800, '公共管理和社会组织在岗职工人数': 144000, '取缔无照经营个数': 6007, '查处取缔无照经营个数': 2126, '参保人数_城镇养老保险参保人数': 657.28, '城镇医疗保险参保人数': 1023.62, '农村养老保险参保人数': 100.5, '户数统计_总户数': 362.63, '有线电视用户数': 313, '互联网用户数': 1014, '刑事案件立案件数': 'A', '刑事案件破案件数': 35.0205575118525, '二氧化硫排放总量_2012年': 195395, 'R&D经费数': 464.69, 'R&D经费与GDP之比': 3, '自来水受益村数': 'A', '村委会个数': 3698, '受理信访举报案件数': 7231, '文化馆': 19, '博物馆': 22, '群众艺术馆': 19, '文化艺术团体': 51, '体育馆': 'A', '城镇最低生活保障人数': 135760, '农村最低生活保障人数': 101447, '贪污贿赂人数': 341, '渎职侵权人数': 56, '财政总收入': 2390.02, '财政总收入增长率': 15.0, '固定资产投资总额增长率': 15.1, '全社会消费品零售总额增长率': 6.0, '进出口总额增长率': 4.2, '实际利用外资金额增长率': 12.1, '规模以上工业企业增加值': 1520.52, '规模以上工业企业产值增加值增长率': 10.1, '国有资产保值增值率': 101.6, '万元GDP综合能源消耗': 0.54, '万元GDP综合能源消耗降低率': 6.0, '城镇化率': 82.3, '城镇家庭居民人均可支配收入增长率': 8.7, '农村家庭居民人均纯收入增长率': 10.8, '居民消费价格指数CPI': 101.9, '工业品出厂价格指数PPI': 96.3, '亿元GDP生产安全事故死亡率': 0.0232721834458473, '十万人工矿商贸从业人员事故死亡率': 'A', '食品质量抽样检测合格率': 98.38, '药品安全抽样合格率': 'A', '工业产品质量抽样合格率': 97.85, '查处农资违法案件的数量': 'A', '查办各类经济违法案件的数量': 250, '查办违法广告的件数': 351, '查办商标侵权案件的件数': 396, '消费者维权案件办理率': 99.64, '出生人口性别比': 'A', '人口出生率': 8.19, '符合政策生育率': 98.45, '年末实有社会组织登记数量': 4729, '万人刑事案件发案件数': nan, '调处各类矛盾纠纷件数': 90028, '成功调处各类矛盾纠纷数': 88230, '受理各类法律援助案件的数量': 4114, '火灾死亡人数': 'A', '接待群众来信来访人次': 13195, '城镇新增就业人数': 48.8, '农村养老保险覆盖率': 27.0444821183499, '新建各类保障性住房面积': '6.1万套', '农村自来水覆盖率（农村安全饮水覆盖率）': 98.98, '人均拥有道路面积': 15.78, '每万人拥有公交汽车数量': 13.41, '有线电视入户率': 88.95, '高中阶段毛入学率': 100, '新农合参合率': 'A', '森林覆盖率': 9.87, '水土流失治理面积': 6400, '工业废水排放达标率': 'A', '工业固体废弃物综合利用率': 98.91, '生活垃圾无害化处理率': 96.23, '城镇生活污水处理率': 100, '城市空气质量指数': 47.9, '城市区域环境噪音指数（市区区域环境噪音平均等效声级值）': 53.6, '违法违纪发案件数': 670, '行政复议案件办结率': 'A', '行政复议案件申请量': 194, '受理行政诉讼的案件数量': 194, '被依法追究责任的领导干部个数': 'A', '主动公开政府信息件数_2011年': 123888, '2012年': 214499, '主动公开政府信息增长率': 73.1394485341599, '依申请公开政府信息件数_2013年': 5146, '2014年': 11399, '依申请公开政府信息增长率': 121.511853867081, '因公开问题申请行政复议的数量': 1074}]
    alias_map = {
        '常住人口': '常住人口数',
        '户籍人口': '户籍人口数',
        '一般预算收入': '一般公共预算收入',
        '城镇居民家庭人均可支配收入': '城镇居民人均可支配收入',
        '农村居民家庭人均纯收入': '农民居民人均可纯收入',
    }

    growth_name_map = {
        'GDP': 'GDP增长率',
        '一般预算收入': '财政总收入增长率',
        '一般公共预算收入': '财政总收入增长率',
    }

    for row in rows_data:
        city_name = row.get('城市') or row.get('城市名称')
        city_name_to_code = get_city_name_to_code()
        area = row.get('area') or row.get('所辖区县名称') or row.get('所辖区域名称') or row.get('区县') or ''
        area = str(area).strip() if area is not None else ''
        city_id = city_name_to_code.get(str(city_name).replace('市',''), 0) if city_name else 0
        city_code_to_province = get_city_code_to_province()
        province_info = city_code_to_province.get(city_id)
        province_id = province_info['province_code'] if province_info else 0

        if not city_id or not area:
            continue

        last_metric_name = None
        for col_name, raw_value in row.items():
            if col_name in ['城市', '城市名称', 'area', '所辖区县名称', '区县', '区县名称', '区县名', 'A']:
                continue

            raw_name = str(col_name).split('__dup', 1)[0].strip()
            if raw_name in ['所辖区域名称', '区域名称']:
                continue

            if raw_name == '增长率':
                name_zh = growth_name_map.get(last_metric_name, '增长率')
            else:
                name_zh = alias_map.get(raw_name, raw_name)
                last_metric_name = raw_name

            value, source, note = extract_cell_fields(raw_value)
            if not has_excel_cell_value(value):
                continue
            source = normalize_data_source(source) or source or DEFAULT_EXCEL_SOURCE
            print(f"处理指标: {name_zh}，值: {value}，来源: {source}")
            name_en = AREA_INDIMAP.get(name_zh)
            if not name_en:
                print(f"未找到指标英文名映射，跳过: {name_zh}")
                continue
            try:
                IndicatorArea.objects.create(
                    year=year,
                    province_id=province_id,
                    city_id=city_id,
                    source=source,
                    input_method=IndicatorArea.InputMethod.EXCEL,
                    value=value,
                    name_en=name_en or '',
                    note=note or '',
                    name_zh=name_zh or '',
                    area=area,
                    input_form=IndicatorArea.InputForm.INPUT,
                    indicator_type=IndicatorArea.IndicatorType.OTHER,
                )
            except IntegrityError as e:
                if 'Duplicate entry' in str(e) or 'UNIQUE constraint failed' in str(e):
                    print(f"跳过重复记录: {year}-{city_id}-{name_en}")
                    continue
                else:
                    print(f"保存指标时出错: {name_zh}, 错误: {e}")
                    continue
                    
            except Exception as e:
                print(f"保存指标时发生未知错误: {name_zh}, 错误: {e}")
                continue       


# === 多指标多城市查询接口 ===
@check_membership
@require_http_methods(['GET'])
def many_indicator_city_query(request):
    # 获取多个指标（用逗号分隔）
    indicator_zh_param = request.GET.get('name_zh', '')
    year = request.GET.get('year')
    citys_param = request.GET.get('city', '')
    province = request.GET.get('province', '')
    
    print("cities=", citys_param)
    print("indicator_zh_param=", indicator_zh_param)
    print("year=", year)
    print("province=", province)
    
    # 解析多个指标（用逗号分隔）
    indicator_zh_list = [ind.strip() for ind in indicator_zh_param.split(',') if ind.strip()]
    
    # 构建指标名转换成英文名
    indicator_en_list = []
    indicator_zh_to_en = {}  # 保存中英文映射
    for indicator_zh in indicator_zh_list:
        indicator_en = INDIMAP.get(indicator_zh)
        if indicator_en:
            indicator_en_list.append(indicator_en)
            indicator_zh_to_en[indicator_en] = indicator_zh
            print(f"指标映射: {indicator_zh} -> {indicator_en}")
        else:
            print(f"未找到指标英文名映射: {indicator_zh}")
    
    if not indicator_en_list:
        return JsonResponse({
            'success': False,
            'message': '未找到有效的指标'
        }, status=400)
    
    # 构建城市名到代码的映射
    city_name_to_code = {}
    for prov in CHINA_REGIONS:
        for city in prov.get('cities', []):
            city_name_to_code[city['name'].replace('市', '')] = int(city['code'])
    
    # 解析多个城市（用逗号分隔）
    city_ids = []
    city_id_to_name = {}  # 保存城市ID到名字的映射
    if citys_param:
        city_names = [name.strip() for name in citys_param.split(',') if name.strip()]        
        for city_name in city_names:
            city_key = city_name.replace('市', '')
            city_id = city_name_to_code.get(city_key)
            if city_id:
                city_ids.append(city_id)
                city_id_to_name[city_id] = city_name
                print(f"城市映射: {city_name} -> {city_id}")
            else:
                print(f"未找到城市代码: {city_name}")
    
    if not city_ids:
        return JsonResponse({
            'success': False,
            'message': '未找到有效的城市'
        }, status=400)
    
    # 构建查询条件
    filters = {
        'name_en__in': indicator_en_list,
        'city_id__in': city_ids,
    }
    if year:
        filters['year'] = year
    
    # 查询数据
    indicators = Indicator.objects.filter(**filters).order_by('city_id', 'name_en')
    
    # 按指标分组返回数据：{ "指标名": [{ "city": "城市名", "val": 值, "unit": 单位 }, ...] }
    result_data = {}
    
    # 初始化：为所有指标和城市创建条目，默认值为 "-"
    for indicator_en in indicator_en_list:
        indicator_zh = indicator_zh_to_en[indicator_en]
        result_data[indicator_zh] = []
        # 为每个城市创建一个条目
        for city_id in city_ids:
            city_name = city_id_to_name.get(city_id) or get_city_name_by_code(city_id)
            result_data[indicator_zh].append({
                'city': city_name,
                'val': '-',
                'unit': INDIMAP_UNIT.get(indicator_en, {}).get('unit', ''),
                'note': '',
                'source': '',
            })
    
    # 填充查询到的数据
    for ind in indicators:
        city_code = ind.city_id
        city_name = city_id_to_name.get(city_code) or get_city_name_by_code(city_code)
        indicator_zh = indicator_zh_to_en.get(ind.name_en, ind.name_zh)
        
        # 获取单位
        unit = INDIMAP_UNIT.get(ind.name_en, {}).get('unit', '')
        
        # 找到对应的条目并更新
        for i, record in enumerate(result_data[indicator_zh]):
            if record['city'] == city_name:
                result_data[indicator_zh][i] = {
                    'city': city_name,
                    'val': ind.value,
                    'unit': unit or '',
                    'note': ind.note or '',
                    'source': ind.source or '',
                }
                break
    
    return JsonResponse({
        'success': True,
        'data': result_data
    })








# ==================== 保存价格配置接口（接收前端修改后的价格数据） ====================
@admin_required
@require_http_methods(["POST"])
def update_pricing_config(request):
    """
    更新价格配置，从前端接收修改后的价格数据并保存到数据库
    POST /dashboard/api/update-pricing-config/
    
    请求体:
        {
            "price_list": [
                { "level": "全国", "userType": "个人用户", "duration": "年", "price": 19999, "days": 365, "category": "national" },
                ...
            ]
        }
    """
    try:
        from apps.coredata.services.pricing_config_service import update_pricing_list

        data = json.loads(request.body)
        price_list = data.get('price_list', [])
        updated_count = update_pricing_list(price_list)
        return JsonResponse({
            'success': True,
            'message': f'成功更新 {updated_count} 条价格配置',
            'updated_count': updated_count
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        print(f"更新价格配置时出错: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'更新价格配置失败: {str(e)}'
        }, status=500)


# ==================== 价格配置接口（返回前端需要的格式） ====================
@require_http_methods(["GET"])
def get_pricing_config(request):
    """
    获取价格配置，返回前端期望的格式
    GET /api/coredata/pricing-config/
    
    返回格式:
        {
            "success": true,
            "data": [
                { "level": "全国", "userType": "个人用户", "duration": "年", "price": 19999, "days": 365, "category": "national" },
                ...
            ]
        }
    """
    try:
        from apps.coredata.services.pricing_config_service import get_pricing_list
        return JsonResponse({
            'success': True,
            'data': get_pricing_list()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


# ==================== 指标配置接口（返回前端需要的指标列表） ====================
@require_http_methods(["GET"])
def org_indicator_config(request):
    """
    获取机构用户可查看的指标列表
    GET /dashboard/api/org-indicator-config/
    """
    try:
        from apps.coredata.services.pricing_config_service import get_indicator_list
        return JsonResponse({
            'success': True,
            'data': get_indicator_list('org')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@require_http_methods(["GET"])
def personal_indicator_config(request):
    """
    获取个人用户可查看的指标列表
    GET /dashboard/api/personal-indicator-config/
    """
    try:
        from apps.coredata.services.pricing_config_service import get_indicator_list
        return JsonResponse({
            'success': True,
            'data': get_indicator_list('personal')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@admin_required
@require_http_methods(["POST"])
def update_indicator_config(request):
    """保存个人/机构指标权限配置。"""
    try:
        from apps.coredata.services.pricing_config_service import replace_indicator_list

        data = json.loads(request.body)
        personal = data.get('personal_indicators', [])
        org = data.get('org_indicators', [])
        personal_count = replace_indicator_list('personal', '个人用户', personal)
        org_count = replace_indicator_list('org', '机构用户', org)
        return JsonResponse({
            'success': True,
            'message': f'已保存指标配置（个人 {personal_count} 项，机构 {org_count} 项）',
            'personal_count': personal_count,
            'org_count': org_count,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '请求数据格式错误'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'保存指标配置失败: {str(e)}'}, status=500)


@require_http_methods(["GET"])
def get_duration_multipliers_api(request):
    """获取时长价格系数（购买页与配置页共用）。"""
    try:
        from apps.coredata.services.pricing_config_service import get_duration_multipliers
        return JsonResponse({'success': True, 'data': get_duration_multipliers()})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e), 'data': {}}, status=500)


@admin_required
@require_http_methods(["POST"])
def update_duration_multipliers_api(request):
    """保存时长价格系数。"""
    try:
        from apps.coredata.services.pricing_config_service import update_duration_multipliers

        data = json.loads(request.body)
        multipliers = data.get('multipliers', {})
        updated = update_duration_multipliers(multipliers)
        return JsonResponse({
            'success': True,
            'message': f'已更新 {updated} 条时长系数',
            'updated_count': updated,
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '请求数据格式错误'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'保存时长系数失败: {str(e)}'}, status=500)


# ==================== 订单与支付 ====================
@login_required_json
@require_http_methods(["POST"])
def create_order_api(request):
    """创建待支付订单（服务端验价 + 支付宝当面付预下单）。"""
    try:
        from django.conf import settings as dj_settings
        from apps.coredata.services.alipay_service import create_face_to_face_payment, is_alipay_mock_mode
        from apps.coredata.services.order_service import create_membership_order

        data = json.loads(request.body)
        user_type = data.get("user_type", "personal")
        duration = data.get("duration", "year")
        permissions = data.get("permissions", [])
        order = create_membership_order(request.user, user_type, duration, permissions)
        pay = create_face_to_face_payment(
            order.order_no,
            order.total_amount,
            subject=f"城策智库-指标查看权限-{order.order_no}",
        )
        return JsonResponse({
            "success": True,
            "message": "订单创建成功，请扫码支付",
            "data": {
                "order_no": order.order_no,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "qr_code": pay.get("qr_code"),
                "expire_at": order.expire_at.isoformat() if order.expire_at else None,
                "pay_timeout_minutes": int(getattr(dj_settings, "ORDER_PAY_TIMEOUT_MINUTES", 30)),
                "alipay_mock": pay.get("mock", False) or is_alipay_mock_mode(),
            },
        })
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "请求数据格式错误"}, status=400)
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"创建订单失败: {str(e)}"}, status=500)


@login_required_json
@require_http_methods(["POST"])
def confirm_order_payment_api(request):
    """已关闭：支付结果由支付宝异步通知处理，请勿手动确认。"""
    return JsonResponse({
        "success": False,
        "message": "请使用支付宝扫码完成支付，系统将自动开通权限",
    }, status=403)


# ==================== 会员激活接口（保留兼容，建议使用 confirm-order-payment） ====================
@login_required
@require_http_methods(["POST"])
def activate_membership(request):
    """直接激活会员（旧接口，仅兼容）。"""
    try:
        from apps.coredata.services.membership_service import apply_membership

        data = json.loads(request.body)
        result = apply_membership(
            request.user,
            duration=data.get("duration", "month"),
            cities=data.get("cities", []),
            indicators=data.get("indicators", []),
        )
        return JsonResponse({
            "success": True,
            "message": f"会员已激活，有效期至 {result['expires_at']}",
            "data": result,
        })
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "请求数据格式错误"}, status=400)
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"激活会员失败: {str(e)}"}, status=500)

