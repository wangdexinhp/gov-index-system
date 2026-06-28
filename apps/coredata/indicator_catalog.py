"""
指标分组目录（查询/录入/校验页共用）

与 INDIMAP / AREA_INDIMAP 中文名对齐；分组名称与录入页左侧树一致。
"""
from typing import Dict, List, TypedDict

from apps.coredata.management.commands.indicator_zh_en import (
    AREA_INDIMAP,
    AREA_INDIMAP_UNIT,
    INDIMAP,
    INDIMAP_UNIT,
)


class IndicatorGroup(TypedDict):
    code: str
    name: str
    indicators: List[str]


INDICATOR_CATALOG_GROUPS: List[IndicatorGroup] = [
    {
        "code": "admin",
        "name": "行政区域数据",
        "indicators": ["市数量", "区数量", "县数量", "辖区面积"],
    },
    {
        "code": "population",
        "name": "人口数据",
        "indicators": [
            "常住人口数", "城镇人口数", "乡村人口数", "户籍人口数", "年末总人口",
            "年末总户数", "15-19岁人口数", "60岁以上人口数", "出生人口性别比", "人口出生率",
        ],
    },
    {
        "code": "economy_structure",
        "name": "经济结构数据",
        "indicators": [
            "年末个体工商户数量", "年末内资企业数", "年末外资企业数", "年末私营企业数",
            "高新技术企业产值", "高新技术企业增加值", "技术合同成交额（交易额）",
            "技术合同成交额（交易额）增长率", "国有资产保值增值率",
            "第二产业增加值占GDP（增量）比重", "第三产业增加值占GDP（增量）比重",
        ],
    },
    {
        "code": "education_tech",
        "name": "教育科技数据",
        "indicators": [
            "有效发明专利量（发明专利有效量）", "每万人发明专利拥有量", "专利授权数量",
            "普通小学专任教师数", "普通中学专任教师数", "普通小学在校学生数",
            "普通中学在校学生数", "高中学在校学生数", "R&D经费",
        ],
    },
    {
        "code": "employment",
        "name": "就业数据",
        "indicators": [
            "采矿（掘)业就业人员人数", "制造业就业人员人数", "采矿（掘)业在岗职工人数",
            "制造业在岗职工人数", "城镇单位职工工资总额",
            "城镇就业人数（城镇单位职工总数（城镇单位就业人数+城镇私营就业人数））",
            "社会从业人员", "机关单位工资总额", "机关单位就业人数",
            "公共管理、社会保障和社会组织工资总额",
            "公共管理、社会保障和社会组织在岗职工人数",
        ],
    },
    {
        "code": "finance",
        "name": "财政指标数据",
        "indicators": [
            "一般公共预算支出", "一般公共服务支出", "科学技术支出", "公共安全支出",
            "文化体育传媒支出", "环保支出", "社会保障和就业支出", "教育支出", "医疗卫生支出",
        ],
    },
    {
        "code": "economic_performance",
        "name": "经济效果数据",
        "indicators": [
            "城镇居民人均消费支出", "城镇食品支出", "农村居民人均消费支出", "农村食品支出",
            "城镇恩格尔系数", "农村恩格尔系数", "城镇登记失业人员数", "城镇登记失业率",
            "能源消耗总量", "万元GDP综合能源消耗", "城镇化率", "城镇居民人均可支配收入",
            "城镇居民人均可支配收入增长率", "农民居民人均可支配收入", "农民居民人均可支配收入增长率",
        ],
    },
    {
        "code": "ecology",
        "name": "生态环保数据",
        "indicators": [
            "万元GDP二氧化硫排放量", "园林绿地面积", "二氧化硫排放总量", "工业二氧化硫排放量",
            "森林覆盖率", "水土流失治理面积", "工业废水排放总量", "工业固体废弃物综合利用率",
            "生活垃圾无害化处理率", "城镇生活污水处理率", "城市空气质量指数",
            "城市区域环境噪音指数（市区区域环境噪音平均等效声级值）", "PM2.5", "PM10",
        ],
    },
    {
        "code": "market_supervision",
        "name": "市场监管数据",
        "indicators": [
            "查出不正当竞争案件数", "生产安全事故死亡人数", "工矿商贸死亡人数",
            "亿元GDP生产安全事故死亡率", "十万人工矿商贸从业人员事故死亡率",
            "食品质量抽样检测合格率", "药品安全抽样合格率", "工业产品质量抽样合格率",
            "查处农资违法案件的数量", "查办违法广告的件数", "查办商标侵权案件的件数",
            "受理消费者维权案件数", "受理消费者投诉案件数", "消费者维权案件办理率",
        ],
    },
    {
        "code": "social_security",
        "name": "社会保障数据",
        "indicators": [
            "城镇职工基本养老保险人数", "城乡居民基本养老保险人数",
            "城镇职工基本医疗保险人数", "城乡居民基本医疗保险人数",
            "城镇最低生活保障人数", "农村最低生活保障人数", "年末实有社会组织登记数量",
            "养老机构床位数", "城镇新增就业人数", "新建保障性住房套数",
        ],
    },
    {
        "code": "healthcare",
        "name": "医疗卫生数据",
        "indicators": ["卫生技术人员数量", "医疗机构病床数"],
    },
    {
        "code": "infrastructure",
        "name": "基础设施数据",
        "indicators": [
            "有线电视用户数", "固定宽带互联网用户数", "自来水受益村数", "村委会个数",
            "每万人拥有公共（电）汽车数量",
        ],
    },
    {
        "code": "public_safety",
        "name": "公共安全数据",
        "indicators": [
            "刑事案件立案件数", "刑事案件破案件数", "受理信访举报案件数",
            "调处各类矛盾纠纷件数", "成功调处各类矛盾纠纷数", "受理各类法律援助案件的数量",
            "火灾死亡人数", "接待群众来信来访人次",
        ],
    },
    {
        "code": "culture_sports",
        "name": "文化体育数据",
        "indicators": ["文化馆、群众艺术馆", "博物馆", "艺术表演团体", "体育场馆", "公共图书馆"],
    },
    {
        "code": "administrative_integrity",
        "name": "行政廉洁数据",
        "indicators": [
            "贪污贿赂人数", "渎职侵权人数", "立案查处违法违纪案件数", "被依法追究责任的领导干部人数",
        ],
    },
    {
        "code": "economic_growth",
        "name": "经济增长数据",
        "indicators": [
            "GDP", "人均GDP", "GDP增长率", "一般公共预算收入", "财政总收入", "财政总收入增长率",
            "固定资产投资总额", "固定资产投资总额增长率", "全社会消费品零售总额",
            "全社会消费品零售总额增长率", "进出口总额", "进出口总额增长率",
            "实际利用外资金额", "实际利用外资金额增长率", "规模以上工业企业增加值",
            "规模以上工业企业增加值增长率",
        ],
    },
    {
        "code": "economic_development",
        "name": "经济发展数据",
        "indicators": ["居民消费价格指数CPI", "工业品出厂价格指数PPI"],
    },
    {
        "code": "public_service",
        "name": "公共服务数据",
        "indicators": ["人均城市道路面积", "高中阶段毛入学率"],
    },
    {
        "code": "law_based_governance",
        "name": "依法行政数据",
        "indicators": ["行政复议案件办结率", "行政复议案件申请量", "行政案件数"],
    },
    {
        "code": "government_affairs_openness",
        "name": "政务公开数据",
        "indicators": [
            "主动公开政府信息件数",
            "依申请公开政府信息件数",
            "因公开问题申请行政复议的数量",
        ],
    },
]

# 区县录入/查询用指标子集
AREA_INDICATOR_CATALOG_GROUPS: List[IndicatorGroup] = [
    {
        "code": "population",
        "name": "人口数据",
        "indicators": ["常住人口数", "户籍人口数"],
    },
    {
        "code": "economic_growth",
        "name": "经济增长数据",
        "indicators": [
            "GDP", "人均GDP", "GDP增长率", "一般公共预算收入", "一般公共预算收入增长率",
            "人均一般公共预算收入", "城镇居民家庭人均可支配收入", "农村居民家庭人均纯收入",
        ],
    },
]

_ZH_TO_EN = {zh: en for zh, en in INDIMAP.items()}
_AREA_ZH_TO_EN = {zh: en for zh, en in AREA_INDIMAP.items()}


def _is_remark_name(name_zh: str) -> bool:
    return name_zh.endswith("备注") or "备注" in name_zh


def build_form_label(name_zh: str, scope: str = "city") -> str:
    """录入表显示名：#指标名(单位)"""
    if scope == "area":
        name_en = _AREA_ZH_TO_EN.get(name_zh)
        unit_map = AREA_INDIMAP_UNIT
    else:
        name_en = _ZH_TO_EN.get(name_zh)
        unit_map = INDIMAP_UNIT
    if not name_en:
        return f"#{name_zh}"
    unit = unit_map.get(name_en, {}).get("unit")
    if unit:
        return f"#{name_zh}({unit})"
    return f"#{name_zh}"


def get_indicator_catalog_groups() -> List[IndicatorGroup]:
    return INDICATOR_CATALOG_GROUPS


def get_area_indicator_catalog_groups() -> List[IndicatorGroup]:
    return AREA_INDICATOR_CATALOG_GROUPS


def get_indicator_unit_map(scope: str = "city") -> Dict[str, str]:
    """{指标中文名: 单位}，供补录/查询页展示。"""
    if scope == "area":
        zh_to_en = _AREA_ZH_TO_EN
        unit_map = AREA_INDIMAP_UNIT
        groups = AREA_INDICATOR_CATALOG_GROUPS
    else:
        zh_to_en = _ZH_TO_EN
        unit_map = INDIMAP_UNIT
        groups = INDICATOR_CATALOG_GROUPS
    result: Dict[str, str] = {}
    for group in groups:
        for name_zh in group["indicators"]:
            if _is_remark_name(name_zh):
                continue
            name_en = zh_to_en.get(name_zh)
            if not name_en:
                continue
            unit = unit_map.get(name_en, {}).get("unit")
            if unit:
                result[name_zh] = unit
    return result


def get_indicator_catalog_dict() -> Dict[str, List[str]]:
    """{分组显示名: [指标中文名, ...]}，供前端 dataDict 使用。"""
    return {group["name"]: list(group["indicators"]) for group in INDICATOR_CATALOG_GROUPS}


def get_area_indicator_catalog_dict() -> Dict[str, List[str]]:
    return {group["name"]: list(group["indicators"]) for group in AREA_INDICATOR_CATALOG_GROUPS}


def get_form_indicator_categories(scope: str = "city") -> Dict[str, List[str]]:
    """{分组 code: [#指标名(单位), ...]}，供录入页弹窗使用（不含备注项）。"""
    groups = INDICATOR_CATALOG_GROUPS if scope == "city" else AREA_INDICATOR_CATALOG_GROUPS
    result: Dict[str, List[str]] = {}
    for group in groups:
        result[group["code"]] = [
            build_form_label(name, scope)
            for name in group["indicators"]
            if not _is_remark_name(name)
        ]
    return result


def get_indicator_group_map() -> Dict[str, str]:
    """{指标中文名: 分组 code}，不含备注项。"""
    result: Dict[str, str] = {}
    for group in INDICATOR_CATALOG_GROUPS:
        for name in group["indicators"]:
            if not _is_remark_name(name):
                result[name] = group["code"]
    return result


def get_group_name_map() -> Dict[str, str]:
    return {group["code"]: group["name"] for group in INDICATOR_CATALOG_GROUPS}


def get_area_group_name_map() -> Dict[str, str]:
    return {group["code"]: group["name"] for group in AREA_INDICATOR_CATALOG_GROUPS}


def get_area_indicator_group_map() -> Dict[str, str]:
    """{指标中文名: 分组 code}，区县指标子集。"""
    result: Dict[str, str] = {}
    for group in AREA_INDICATOR_CATALOG_GROUPS:
        for name in group["indicators"]:
            if not _is_remark_name(name):
                result[name] = group["code"]
    return result
