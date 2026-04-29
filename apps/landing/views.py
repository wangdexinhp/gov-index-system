from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS

@require_http_methods(['GET'])
def home(request):
    features = [
        {
            'title': 'Dashboard Intuitivo',
            'description': 'Panel de control fácil de usar con todas tus métricas importantes.',
            'icon': 'chart-bar'
        },
        {
            'title': 'Autenticación Segura',
            'description': 'Sistema de autenticación robusto con verificación de email.',
            'icon': 'shield-check'
        },
        {
            'title': 'Diseño Responsive',
            'description': 'Interfaz moderna que funciona perfectamente en todos los dispositivos.',
            'icon': 'device-mobile'
        },
        {
            'title': 'Suscripciones Flexibles',
            'description': 'Sistema de pagos seguro con Stripe para gestionar suscripciones.',
            'icon': 'credit-card'
        }
    ]
    
    pricing = {
        'monthly_price': '9.99',
        'features': [
            'Acceso completo al dashboard',
            'Soporte prioritario',
            'Características premium',
            'Actualizaciones ilimitadas',
            'API access',
            'Backups diarios'
        ]
    }
    
    return render(request, 'landing/home.html', {
        'features': features,
        'pricing': pricing,
    })

@require_http_methods(['GET'])
def pricing(request):
    return render(request, 'landing/indic_order.html')

@require_http_methods(['GET'])
def features(request):
    return render(request, 'landing/features.html') 


# ==================== 购买页面城市数据 API ====================

@require_http_methods(['GET'])
def municipality_city(request):
    """
    获取直辖市列表
    返回格式: [
        {"name": "北京市", "code": "110100"},
        {"name": "天津市", "code": "120100"},
        {"name": "上海市", "code": "310100"},
        {"name": "重庆市", "code": "500100"},
    ]
    """
    try:
        municipalities = []
        for province in CHINA_REGIONS:
            # 直辖市：北京市、天津市、上海市、重庆市
            if province['province_name'] in ('北京市', '天津市', '上海市', '重庆市'):
                for city in province.get('cities', []):
                    municipalities.append({
                        'name': city['name'],
                        'code': city['code'],
                    })
        return JsonResponse({
            'success': True,
            'data': municipalities
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })


@require_http_methods(['GET'])
def not_municipality_city(request):
    """
    获取非直辖市的城市列表（普通地级市）
    返回格式: [
        {"name": "石家庄市", "code": "130100"},
        {"name": "唐山市", "code": "130200"},
        ...
    ]
    """
    try:
        cities = []
        municipality_names = ('北京市', '天津市', '上海市', '重庆市')
        for province in CHINA_REGIONS:
            if province['province_name'] not in municipality_names:
                for city in province.get('cities', []):
                    cities.append({
                        'name': city['name'],
                        'code': city['code'],
                    })
        return JsonResponse({
            'success': True,
            'data': cities
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'data': []
        })
