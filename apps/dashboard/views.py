from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse  
import json
from apps.coredata.models.indicator import Indicator
from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS
from apps.coredata.management.commands.indicator_zh_en import INDIMAP
from apps.coredata.utils.mapper import get_city_name_to_code, get_province_name_to_code,get_city_code_to_province

import pandas as pd
from datetime import datetime

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
            source = group.get('source')
            note = group.get('note')
            name_zh = group.get('name_zh')
            name_en = INDIMAP.get(name_zh)

            Indicator.objects.create(
                year=year,
                province_id=province_id,
                city_id=city_id,
                source=source or '',
                value=value or 0,
                name_en=name_en or '',
                note=note or '',
                name_zh= name_zh or '',  # 备注直接写入 name_zh
                input_form=Indicator.InputForm.INPUT,
                indicator_type=Indicator.IndicatorType.OTHER,
            )

@login_required
@require_http_methods(['GET'])
def single_indicator_query(request):

    indicator_en = request.GET.get('name_en')
    indicator_zh = request.GET.get('name_zh')
    start_year = request.GET.get('start_year')
    end_year = request.GET.get('end_year')
    city_name = request.GET.get('city')
    province_name = request.GET.get('province')

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
    if indicator_zh:
        filters['name_zh'] = indicator_zh
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
        })
    return JsonResponse({
        'success': True,
        'data': data
    })



@login_required
@require_http_methods(['POST'])
def upload_excel(request):
    """处理Excel文件上传"""
    try:
        year = request.POST.get('year')
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            return JsonResponse({
                'success': False,
                'message': '未上传文件'
            }, status=400)
        # 这里可以使用 pandas 或 openpyxl 等库来处理 Excel 文件
        # 创建Excel写入器
        tmp_excel_file = f'/mnt/excel/temp_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        with pd.ExcelWriter(tmp_excel_file, engine='openpyxl') as writer:
            raw_data = pd.read_excel(excel_file, sheet_name="Sheet1", header=None)
            print(f"=== 接收到的Excel数据 ===\n{raw_data.head()}")
            print(f"数据条数: {len(raw_data)}")


            headers = []
            for col_idx in range(raw_data.shape[1]):
                col_headers = []
                
                # 第1行
                level1 = raw_data.iloc[0, col_idx]
                if pd.notna(level1):
                    col_headers.append(str(level1).strip())
                
                # 第2行
                level2 = raw_data.iloc[1, col_idx]
                if pd.notna(level2) and str(level2).strip():
                    col_headers.append(str(level2).strip())
                
                # 创建列名
                if col_headers:
                    col_name = '_'.join(col_headers)
                else:
                    col_name = f'Column_{col_idx+1}'
                
                headers.append(col_name)
            
            data_df = raw_data.iloc[3:, :].reset_index(drop=True)
            data_df.columns = headers
            # 保存到新文件
            data_df.to_excel(writer, sheet_name="Sheet1", index=False)
        # 保存数据到数据库
        tmp_raw_data = pd.read_excel(tmp_excel_file, sheet_name="Sheet1", header=None)
        save_df_to_database(rows_data=tmp_raw_data.to_dict(orient='records'), year=year)

        return JsonResponse({
            'success': True,
            'message': "成功处理Excel文件"
        })

    except Exception as e:
        print(f"处理Excel文件时出错: {str(e)}")
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
        for col_name, value in row.items():
            if col_name in ['城市', 'A']:
                continue  
            name_zh = col_name
            print(f"处理指标: {name_zh}，值: {value}")
            name_en = INDIMAP.get(name_zh)
            if not name_en:
                print(f"未找到指标英文名映射，跳过: {name_zh}")
                continue
        
            Indicator.objects.create(
                year=year,
                province_id=province_id,
                city_id=city_id,
                source='INPUT',
                value=value or 0,
                name_en=name_en or '',
                note= '',
                name_zh= name_zh or '',  # 备注直接写入 name_zh
                input_form=Indicator.InputForm.INPUT,
                indicator_type=Indicator.IndicatorType.OTHER,
            )
    
