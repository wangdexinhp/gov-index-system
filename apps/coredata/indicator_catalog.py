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
        "code": "public_safety",
        "name": "公共安全数据",
        "indicators": [
            "亿元GDP生产安全事故死亡率",
            "十万人工矿商贸从业人员事故死亡率",
            "工矿商贸死亡人数",
            "火灾死亡人数",
            "接待群众来信来访人次",
            "刑事案件立案件数",
            "刑事案件破案件数",
            "成功调处各类矛盾纠纷数",
            "生产安全事故死亡人数",
            "受理各类法律援助案件的数量",
            "调处各类矛盾纠纷件数",
            "万人刑事案件发案件数",
            "万人刑事案件破案件数",
        ],
    },
    {
        "code": "finance",
        "name": "财政指标数据",
        "indicators": [
            "财政总收入",
            "财政总收入增长率",
            "财政总支出",
            "公共安全支出",
            "环保支出",
            "教育支出",
            "科学技术支出",
            "社会保障和就业支出",
            "文化体育传媒支出",
            "医疗卫生支出",
            "一般公共预算收入",
            "一般公共预算支出",
            "一般公共服务支出",
        ],
    },
    {
        "code": "infrastructure",
        "name": "基础设施数据",
        "indicators": [
            "固定宽带互联网用户数",
            "每万人拥有公共（电）汽车数量",
            "农村自来水覆盖率（农村安全饮水覆盖率）",
            "人均城市道路面积",
            "有线电视入户率",
            "有线电视用户数",
            "自来水受益村数",
            "村委会个数",
        ],
    },
    {
        "code": "education_tech",
        "name": "教育科技数据",
        "indicators": [
            "R&D经费",
            "R&D经费与GDP之比",
            "专利授权量",
            "专任教师数",
            "高中阶段教育在校生人数",
            "高中阶段毛入学率",
            "普通小学在校生人数",
            "普通中学在校生人数",
            "普通小学专任教师数",
            "普通中学专任教师数",
        ],
    },
    {
        "code": "economy_structure",
        "name": "经济结构数据",
        "indicators": [
            "第三产业增加值占GDP（增量）比重",
            "第二产业增加值占GDP（增量）比重",
            "高新技术企业产值",
            "高新技术企业增加值",
            "技术合同成交额",
            "技术合同成交额增长率",
            "每万人发明专利拥有量",
            "年末实有内资企业",
            "年末实有企业数",
            "年末实有农民专业合作社",
            "年末实有外资企业",
            "年末实有个体工商户",
            "有效发明专利量",
            "国有资产保值增值率",
        ],
    },
    {
        "code": "economic_growth",
        "name": "经济增长数据",
        "indicators": [
            "GDP",
            "GDP增长率",
            "规模以上工业企业产值增加值增长率",
            "规模以上工业企业增加值",
            "固定资产投资总额",
            "固定资产投资总额增长率",
            "进出口总额",
            "进出口总额增长率",
            "人均GDP",
            "全社会消费品零售总额",
            "全社会消费品零售总额增长率",
            "实际利用外资金额",
            "实际利用外资金额增长率",
        ],
    },
    {
        "code": "economic_performance",
        "name": "经济效果数据",
        "indicators": [
            "城镇居民人均可支配收入",
            "城镇居民人均可支配收入增长率",
            "城镇居民人均消费支出",
            "城镇恩格尔系数",
            "城镇食品支出",
            "工业品出厂价格指数PPI",
            "居民消费价格指数CPI",
            "农村居民人均可支配收入",
            "农村居民人均可支配收入增长率",
            "农村居民人均消费支出",
            "农村恩格尔系数",
            "农村食品支出",
        ],
    },
    {
        "code": "employment",
        "name": "就业数据",
        "indicators": [
            "采矿（掘）业就业人员人数",
            "采矿（掘）业在岗职工人数",
            "城镇登记失业率",
            "城镇登记失业人员数",
            "城镇单位职工工资总额",
            "城镇就业人数（城镇单位职工总数）",
            "城镇新增就业人数",
            "公共管理、社会保障和社会组织工资总额",
            "公共管理、社会保障和社会组织在岗职工人数",
            "机关单位工资总额",
            "机关单位就业人数",
            "社会从业人员",
            "制造业就业人员人数",
            "制造业在岗职工人数",
        ],
    },
    {
        "code": "population",
        "name": "人口数据",
        "indicators": [
            "15-19岁人口数",
            "60岁以上老人人口数",
            "常住人口",
            "城镇化率",
            "出生人口性别比",
            "户籍人口",
            "年末总户数",
            "年末总人口",
            "人口出生率",
            "城镇人口",
            "乡村人口",
        ],
    },
    {
        "code": "social_security",
        "name": "社会保障数据",
        "indicators": [
            "城乡居民基本养老保险人数",
            "城乡居民基本医疗保险人数",
            "城镇职工基本养老保险人数",
            "城镇职工基本医疗保险人数",
            "城镇最低生活保障人数",
            "农村最低生活保障人数",
            "年末实有社会组织登记数量",
            "新建保障性住房套数",
            "养老机构床位数",
        ],
    },
    {
        "code": "ecology",
        "name": "生态环保数据",
        "indicators": [
            "PM10",
            "PM2.5",
            "城市空气质量指数",
            "城市区域环境噪音指数",
            "二氧化硫排放总量",
            "工业二氧化硫排放量",
            "工业废水排放总量",
            "工业固体废弃物综合利用率",
            "森林覆盖率",
            "生活垃圾无害化处理率",
            "水土流失治理面积",
            "城镇生活污水处理率",
            "能源消费总量",
            "万元GDP综合能源消耗",
            "万元GDP综合能源消耗降低率",
            "园林绿地面积",
        ],
    },
    {
        "code": "market_supervision",
        "name": "市场监管数据",
        "indicators": [
            "查办各类经济违法案件的数量",
            "查办违法广告的件数",
            "查办商标侵权案件的件数",
            "查处农资违法案件的数量",
            "查出不正当竞争案件数",
            "工业产品质量抽样合格率",
            "食品质量抽样检测合格率",
            "受理消费者投诉案件数",
            "受理消费者维权案件数",
            "消费者维权案件办理率",
            "药品安全抽样合格率",
        ],
    },
    {
        "code": "culture_sports",
        "name": "文化体育数据",
        "indicators": [
            "博物馆",
            "公共图书馆",
            "体育场馆",
            "文化馆、群众艺术馆",
            "艺术表演团体",
        ],
    },
    {
        "code": "admin",
        "name": "行政区域数据",
        "indicators": [
            "辖区面积",
            "县个数",
            "区个数",
            "市个数",
        ],
    },
    {
        "code": "administrative_integrity",
        "name": "行政廉洁数据",
        "indicators": [
            "被依法追究责任的领导干部人数",
            "渎职侵权人数",
            "贪污贿赂人数",
            "职务犯罪人数",
            "立案查处违法违纪案件数",
        ],
    },
    {
        "code": "law_based_governance",
        "name": "依法行政数据",
        "indicators": [
            "行政案件数",
            "行政复议案件办结率",
            "行政复议案件申请量",
        ],
    },
    {
        "code": "government_affairs_openness",
        "name": "政务公开数据",
        "indicators": [
            "主动公开政府信息件数",
            "主动公开政府信息增长率",
            "依申请公开政府信息件数",
            "依申请公开政府信息增长率",
            "因公开问题申请行政复议的数量",
        ],
    },
    {
        "code": "healthcare",
        "name": "医疗卫生数据",
        "indicators": [
            "卫生技术人员数量",
            "医疗机构病床数",
        ],
    },
]

# 区县录入/查询用指标子集
AREA_INDICATOR_CATALOG_GROUPS: List[IndicatorGroup] = [
    {
        "code": "population",
        "name": "人口数据",
        "indicators": ["常住人口", "户籍人口"],
    },
    {
        "code": "economic_growth",
        "name": "经济增长数据",
        "indicators": [
            "GDP", "人均GDP", "GDP增长率", "一般公共预算收入", "一般公共预算收入增长率",
            "人均一般公共预算收入", "城镇居民人均可支配收入", "农村居民人均可支配收入",
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
