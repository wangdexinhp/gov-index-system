from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS
from apps.coredata.management.commands.indicator_zh_en import INDIMAP
# # 构建映射
# city_name_to_code = {}
# province_name_to_code = {}
# province_code_by_city_code = {}


# for prov in CHINA_REGIONS:
#     province_name = prov['province_name']
#     province_code = int(prov['province_code'])
#     province_name_to_code[province_name] = province_code
    
#     # 兼容"北京市"/"北京"
#     if province_name.endswith('市'):
#         province_name_to_code[province_name.replace('市', '')] = province_code
    
#     for city in prov.get('cities', []):
#         city_name_to_code[city['name'].replace('市', '')] = int(city['code'])

# print(f"✓ 应用启动: 已加载 {len(city_name_to_code)} 个城市映射, {len(province_name_to_code)} 个省份映射")


# # 导出全局变量
# __all__ = ['city_name_to_code', 'province_name_to_code']




# 构建映射
city_code_to_province = {}
city_name_to_code = {}
province_name_to_code = {}
province_code_to_name = {}  

for prov in CHINA_REGIONS:
    province_name = prov['province_name']
    province_code = prov['province_code']
    
    # 省份映射
    province_name_to_code[province_name] = province_code
    province_code_to_name[province_code] = province_name
    
    # 兼容处理
    def add_province_alias(full_name, short_name):
        province_name_to_code[short_name] = province_code
        province_name_to_code[full_name] = province_code
    
    if province_name.endswith('市'):
        add_province_alias(province_name, province_name.replace('市', ''))
    elif province_name.endswith('省'):
        add_province_alias(province_name, province_name.replace('省', ''))
    elif province_name.endswith('自治区'):
        short_name = province_name.replace('自治区', '')
        if short_name.endswith('壮族'):
            short_name = short_name.replace('壮族', '')
        elif short_name.endswith('维吾尔'):
            short_name = short_name.replace('维吾尔', '')
        elif short_name.endswith('回族'):
            short_name = short_name.replace('回族', '')
        add_province_alias(province_name, short_name)
    
    # 城市映射
    for city in prov.get('cities', []):
        city_name = city['name']
        city_code = city['code']
        
        # 城市名到代码
        city_name_to_code[city_name.replace('市', '')] = city_code
        
        # 城市代码到省份信息
        city_code_to_province[city_code] = {
            'province_code': province_code,
            'province_name': province_name,
            'city_name': city_name,
            'is_direct_city': province_name in ['北京市', '上海市', '天津市', '重庆市']
        }

print(f"✓ 区域映射初始化完成: {len(city_code_to_province)} 个城市, {len(province_name_to_code)} 个省份")

# 导出
__all__ = [
    'city_code_to_province',
    'city_name_to_code', 
    'province_name_to_code',
    'province_code_to_name',
]