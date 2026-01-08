# apps/coredata/utils/region_utils.py
"""区域映射工具 - 简化版"""
from apps.coredata.management.commands.import_china_regions import CHINA_REGIONS

# 缓存映射
_city_code_to_province = None
_city_name_to_code = None
_province_name_to_code = None
_province_code_to_name = None

def _init_mappings():
    """初始化所有映射（内部函数）"""
    global _city_code_to_province, _city_name_to_code, _province_name_to_code, _province_code_to_name
    
    if _city_code_to_province is not None:
        return
    
    _city_code_to_province = {}
    _city_name_to_code = {}
    _province_name_to_code = {}
    _province_code_to_name = {}
    
    for prov in CHINA_REGIONS:
        province_name = prov['province_name']
        province_code = prov['province_code']
        
        # 省份映射
        _province_name_to_code[province_name] = province_code
        _province_code_to_name[province_code] = province_name
        
        # 省份别名
        if province_name.endswith('市'):
            _province_name_to_code[province_name.replace('市', '')] = province_code
        elif province_name.endswith('省'):
            _province_name_to_code[province_name.replace('省', '')] = province_code
        elif province_name.endswith('自治区'):
            short_name = province_name.replace('自治区', '')
            if short_name.endswith('壮族'):
                short_name = short_name.replace('壮族', '')
            elif short_name.endswith('维吾尔'):
                short_name = short_name.replace('维吾尔', '')
            elif short_name.endswith('回族'):
                short_name = short_name.replace('回族', '')
            _province_name_to_code[short_name] = province_code
        
        # 城市映射
        for city in prov.get('cities', []):
            city_name = city['name']
            city_code = city['code']
            
            _city_name_to_code[city_name.replace('市', '')] = city_code
            _city_code_to_province[city_code] = {
                'province_code': province_code,
                'province_name': province_name,
                'city_name': city_name
            }
    
    print(f"✓ 区域映射初始化: {len(_city_code_to_province)} 城市, {len(_province_name_to_code)} 省份")

# ========== 4个基础函数 ==========

def get_city_code_to_province():
    """城市代码 → 省份信息"""
    _init_mappings()
    return _city_code_to_province

def get_city_name_to_code():
    """城市名 → 城市代码"""
    _init_mappings()
    return _city_name_to_code

def get_province_name_to_code():
    """省份名 → 省份代码"""
    _init_mappings()
    return _province_name_to_code

def get_province_code_to_name():
    """省份代码 → 省份名"""
    _init_mappings()
    return _province_code_to_name

# ========== 4个实用查询函数 ==========

def get_province_by_city_code(city_code):
    """通过城市代码获取省份信息"""
    _init_mappings()
    return _city_code_to_province.get(str(city_code))

def get_city_code_by_name(city_name):
    """通过城市名获取城市代码"""
    _init_mappings()
    clean_name = str(city_name).replace('市', '').strip()
    return _city_name_to_code.get(clean_name)

def get_province_code_by_name(province_name):
    """通过省份名获取省份代码"""
    _init_mappings()
    return _province_name_to_code.get(str(province_name).strip())

def get_province_name_by_code(province_code):
    """通过省份代码获取省份名"""
    _init_mappings()
    return _province_code_to_name.get(str(province_code))