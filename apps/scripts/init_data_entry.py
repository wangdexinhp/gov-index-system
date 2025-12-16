# scripts/init_data_entry.py
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.data_entry.models import Province, City, IndicatorCategory, Indicator


def init_provinces_and_cities():
    """初始化省份和城市数据"""
    provinces_data = [
        {'code': '110000', 'name': '北京市'},
        {'code': '310000', 'name': '上海市'},
        {'code': '440000', 'name': '广东省'},
        {'code': '320000', 'name': '江苏省'},
        {'code': '330000', 'name': '浙江省'},
    ]

    cities_data = {
        '北京市': [
            {'code': '110100', 'name': '北京市'},
        ],
        '上海市': [
            {'code': '310100', 'name': '上海市'},
        ],
        '广东省': [
            {'code': '440100', 'name': '广州市'},
            {'code': '440300', 'name': '深圳市'},
            {'code': '440400', 'name': '珠海市'},
        ],
        '江苏省': [
            {'code': '320100', 'name': '南京市'},
            {'code': '320500', 'name': '苏州市'},
            {'code': '320200', 'name': '无锡市'},
        ],
        '浙江省': [
            {'code': '330100', 'name': '杭州市'},
            {'code': '330200', 'name': '宁波市'},
            {'code': '330300', 'name': '温州市'},
        ],
    }

    for prov_data in provinces_data:
        province, created = Province.objects.get_or_create(
            code=prov_data['code'],
            defaults={'name': prov_data['name']}
        )

        if province.name in cities_data:
            for city_data in cities_data[province.name]:
                City.objects.get_or_create(
                    code=city_data['code'],
                    province=province,
                    defaults={'name': city_data['name']}
                )

    print(f"初始化了 {Province.objects.count()} 个省份和 {City.objects.count()} 个城市")


def init_indicators():
    """初始化指标数据"""
    categories = [
        {'code': 'ECON', 'name': '经济发展', 'order': 1},
        {'code': 'ENV', 'name': '环境保护', 'order': 2},
        {'code': 'SOC', 'name': '社会民生', 'order': 3},
        {'code': 'GOV', 'name': '政府治理', 'order': 4},
        {'code': 'INFRA', 'name': '基础设施', 'order': 5},
    ]

    indicators = [
        # 经济发展指标
        {'category': 'ECON', 'code': 'GDP', 'name': '地区生产总值（亿元）', 'data_type': 'number', 'unit': '亿元'},
        {'category': 'ECON', 'code': 'GDP_PERCAPITA', 'name': '人均地区生产总值（元）', 'data_type': 'number',
         'unit': '元'},
        {'category': 'ECON', 'code': 'GDP_GROWTH', 'name': '地区生产总值增长率（%）', 'data_type': 'percentage',
         'unit': '%'},
        {'category': 'ECON', 'code': 'INDUSTRY_STRUCTURE', 'name': '三次产业结构', 'data_type': 'text', 'unit': ''},
        {'category': 'ECON', 'code': 'FIXED_INVESTMENT', 'name': '固定资产投资（亿元）', 'data_type': 'number',
         'unit': '亿元'},

        # 环境保护指标
        {'category': 'ENV', 'code': 'AIR_QUALITY_GOOD_DAYS', 'name': '空气质量优良天数（天）', 'data_type': 'integer',
         'unit': '天'},
        {'category': 'ENV', 'code': 'PM25', 'name': 'PM2.5年均浓度（μg/m³）', 'data_type': 'number', 'unit': 'μg/m³'},
        {'category': 'ENV', 'code': 'WATER_QUALITY', 'name': '地表水优良比例（%）', 'data_type': 'percentage',
         'unit': '%'},
        {'category': 'ENV', 'code': 'FOREST_COVERAGE', 'name': '森林覆盖率（%）', 'data_type': 'percentage', 'unit': '%'},
        {'category': 'ENV', 'code': 'ENERGY_CONSUMPTION', 'name': '单位GDP能耗（吨标准煤/万元）', 'data_type': 'number',
         'unit': '吨标准煤/万元'},

        # 社会民生指标（示例20个）
        {'category': 'SOC', 'code': 'POPULATION', 'name': '常住人口（万人）', 'data_type': 'number', 'unit': '万人'},
        {'category': 'SOC', 'code': 'URBANIZATION_RATE', 'name': '城镇化率（%）', 'data_type': 'percentage', 'unit': '%'},
        {'category': 'SOC', 'code': 'DISPOSABLE_INCOME', 'name': '居民人均可支配收入（元）', 'data_type': 'number',
         'unit': '元'},
        {'category': 'SOC', 'code': 'CONSUMPTION_EXPENDITURE', 'name': '居民人均消费支出（元）', 'data_type': 'number',
         'unit': '元'},
        {'category': 'SOC', 'code': 'UNEMPLOYMENT_RATE', 'name': '城镇登记失业率（%）', 'data_type': 'percentage',
         'unit': '%'},
    ]

    # 创建分类
    category_dict = {}
    for cat_data in categories:
        category, created = IndicatorCategory.objects.get_or_create(
            code=cat_data['code'],
            defaults={'name': cat_data['name'], 'order': cat_data['order']}
        )
        category_dict[cat_data['code']] = category

    # 创建指标
    for idx, ind_data in enumerate(indicators):
        Indicator.objects.get_or_create(
            code=ind_data['code'],
            defaults={
                'category': category_dict[ind_data['category']],
                'name': ind_data['name'],
                'data_type': ind_data['data_type'],
                'unit': ind_data.get('unit', ''),
                'order': idx + 1,
                'is_active': True,
            }
        )

    print(f"初始化了 {IndicatorCategory.objects.count()} 个分类和 {Indicator.objects.count()} 个指标")


if __name__ == '__main__':
    init_provinces_and_cities()
    init_indicators()
    print("数据录入系统初始化完成！")