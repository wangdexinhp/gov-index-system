"""
计算型指标定义（来自 Excel「计算指标数据表」）。

name_en 为入库主键；已与 INDIMAP 对齐的指标复用既有英文码，不另造重复码。
expr 中的变量名为同年度 INPUT 依赖的 name_en；needs_prev_year=True 时，
上年同名指标以 prev_<name_en> 注入。expr=None 表示已注册但暂不自动计算。
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class CalcIndicator(TypedDict):
    name_en: str
    name_zh: str
    unit: str
    deps: list[str]
    expr: str | None
    needs_prev_year: NotRequired[bool]


CALC_INDICATORS: list[CalcIndicator] = [
    {
        "name_en": "avg_revene",
        "name_zh": "人均财政收入",
        "unit": "元",
        "deps": ["total_revenue", "long_term_pop"],
        "expr": "total_revenue * 10000 / long_term_pop",
    },
    {
        "name_en": "avg_assets_investment",
        "name_zh": "人均固定资产投资",
        "unit": "元",
        "deps": ["fixed_assets_investment_total", "long_term_pop"],
        "expr": "fixed_assets_investment_total * 10000 / long_term_pop",
    },
    {
        "name_en": "avg_rate_retail_sales_consumer_goods",
        "name_zh": "人均消费品零售总额",
        "unit": "元",
        "deps": ["retail_sales_consumer_goods", "long_term_pop"],
        "expr": "retail_sales_consumer_goods * 10000 / long_term_pop",
    },
    {
        "name_en": "have_10thousand_person_company_num",
        "name_zh": "十万人拥有企业数",
        "unit": "个/十万人",
        "deps": [
            "domestic_company_year_end",
            "foreign_company_year_end",
            "private_company_year_end",
            "long_term_pop",
        ],
        "expr": (
            "(domestic_company_year_end + foreign_company_year_end"
            " + private_company_year_end) / long_term_pop * 10"
        ),
    },
    {
        "name_en": "rate_in_gdp_high_tech_company",
        "name_zh": "高新技术企业经济贡献率",
        "unit": "%",
        "deps": ["incre_value_high_tech_company", "gdp"],
        "expr": "incre_value_high_tech_company / gdp * 100",
    },
    {
        "name_en": "labor_production_rate",
        "name_zh": "全社会劳动生产率",
        "unit": "万元/人",
        "deps": ["gdp", "social_employment_pop"],
        "expr": "gdp / social_employment_pop",
    },
    {
        "name_en": "engel",
        "name_zh": "恩格尔系数",
        "unit": "%",
        "deps": ["city_food_consumption_expend", "city_avg_consumption_expend"],
        "expr": "city_food_consumption_expend / city_avg_consumption_expend * 100",
    },
    {
        "name_en": "cancel_rate_no_license_company",
        "name_zh": "取缔无照经营个数/登记企业个数（无照经营取缔查处率）",
        "unit": "%",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "social_org_num_10thousand",
        "name_zh": "每万人年末实有社会组织登记数量",
        "unit": "个/万人",
        "deps": ["social_org_num_year_end", "long_term_pop"],
        "expr": "social_org_num_year_end / long_term_pop",
    },
    {
        "name_en": "criminal_case_per_10thousand",
        "name_zh": "万人刑事案件发案件数",
        "unit": "件/万人",
        "deps": ["file_criminal_case_num", "long_term_pop"],
        "expr": "file_criminal_case_num / long_term_pop",
    },
    {
        "name_en": "solve_criminal_case_per_10thousand",
        "name_zh": "万人刑事案件破案件数",
        "unit": "件/万人",
        "deps": ["solve_criminal_case_num", "long_term_pop"],
        "expr": "solve_criminal_case_num / long_term_pop",
    },
    {
        "name_en": "mediation_conflict_dispute_100thousand",
        "name_zh": "十万人调处各类矛盾纠纷件数",
        "unit": "件/十万人",
        "deps": ["mediation_conflict_dispute_num", "long_term_pop"],
        "expr": "mediation_conflict_dispute_num / long_term_pop * 10",
    },
    {
        "name_en": "legal_aid_case_10thousand",
        "name_zh": "每万人受理各类法律援助案件的数量",
        "unit": "件/万人",
        "deps": ["legal_aid_case_num", "long_term_pop"],
        "expr": "legal_aid_case_num / long_term_pop",
    },
    {
        "name_en": "receive_public_visit_10thousand",
        "name_zh": "每万人接待群众来信来访人次",
        "unit": "件次/万人",
        "deps": ["receive_public_visit_num", "long_term_pop"],
        "expr": "receive_public_visit_num / long_term_pop",
    },
    {
        "name_en": "social_security_budget_expend_rate",
        "name_zh": "社会保障和就业支出占地方财政一般预算支出的比重",
        "unit": "%",
        "deps": ["social_security_budget_expend", "public_budget_expend"],
        "expr": "social_security_budget_expend / public_budget_expend * 100",
    },
    {
        "name_en": "city_insurance_rate",
        "name_zh": "城镇社会保险覆盖率",
        "unit": "%",
        "deps": ["employees_pension_insurance", "city_work_pop_total"],
        "expr": "employees_pension_insurance / city_work_pop_total * 100",
    },
    {
        "name_en": "city_minimum_living_standard_rate",
        "name_zh": "城镇最低生活保障覆盖率",
        "unit": "%",
        "deps": ["city_minimum_living_standard_pop", "city_pop"],
        "expr": "city_minimum_living_standard_pop / (city_pop * 10000) * 100",
    },
    {
        "name_en": "city_work_new_pop_rate",
        "name_zh": "城镇新增就业人数占比（城镇新增就业人数/城镇就业人数）",
        "unit": "%",
        "deps": ["incre_city_employment_num", "city_work_pop_total"],
        "expr": "incre_city_employment_num / city_work_pop_total * 100",
    },
    {
        "name_en": "rural_tap_water_coverage_rate",
        "name_zh": "农村自来水覆盖率（农村安全饮水覆盖率）",
        "unit": "%",
        "deps": ["tap_water_village_num", "government_village_num"],
        "expr": "tap_water_village_num / government_village_num * 100",
    },
    {
        "name_en": "cable_tv_household_rate",
        "name_zh": "有线电视入户率",
        "unit": "%",
        "deps": ["cable_tv_user_num", "household_num_year_end"],
        "expr": "cable_tv_user_num / household_num_year_end * 100",
    },
    {
        "name_en": "internet_100person_num",
        "name_zh": "每百人互联网用户数",
        "unit": "户/百人",
        "deps": ["broadband_user_num", "long_term_pop"],
        "expr": "broadband_user_num / long_term_pop * 100",
    },
    {
        "name_en": "bus_per_10thousand",
        "name_zh": "每万人拥有公共（电）汽车数量",
        "unit": "辆/万人",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "education_budget_expend_rate",
        "name_zh": "教育支出占地方财政一般预算支出比重",
        "unit": "%",
        "deps": ["education_budget_expend", "public_budget_expend"],
        "expr": "education_budget_expend / public_budget_expend * 100",
    },
    {
        "name_en": "school_teacher_10thousand_num",
        "name_zh": "普通中学小学在校学生每万人拥有的专任教师数",
        "unit": "人/万人",
        "deps": [
            "primary_school_teacher_num",
            "middle_school_teacher_num",
            "primary_school_student_num",
            "middle_school_student_num",
        ],
        "expr": (
            "(primary_school_teacher_num + middle_school_teacher_num) * 10000"
            " / (primary_school_student_num + middle_school_student_num)"
        ),
    },
    {
        "name_en": "rd_funds_gdp_ratio",
        "name_zh": "R&D经费与GDP之比",
        "unit": "%",
        "deps": ["rd_funds", "gdp"],
        "expr": "rd_funds / gdp * 100",
    },
    {
        "name_en": "medical_staff_10thousand_num",
        "name_zh": "万人卫生机构卫生技术人员数量",
        "unit": "人/万人",
        "deps": ["medical_staff_num", "long_term_pop"],
        "expr": "medical_staff_num / long_term_pop",
    },
    {
        "name_en": "medical_staff_10thousand_incre_rate",
        "name_zh": "万人卫生机构卫生技术人员增长率",
        "unit": "%",
        "deps": ["medical_staff_num", "long_term_pop"],
        "expr": (
            "((medical_staff_num / long_term_pop)"
            " - (prev_medical_staff_num / prev_long_term_pop))"
            " / (prev_medical_staff_num / prev_long_term_pop) * 100"
        ),
        "needs_prev_year": True,
    },
    {
        "name_en": "medical_bed_10thousand_num",
        "name_zh": "万人医疗机构病床数",
        "unit": "张/万人",
        "deps": ["medical_bed_num", "long_term_pop"],
        "expr": "medical_bed_num / long_term_pop",
    },
    {
        "name_en": "medical_bed_10thousand_incre_rate",
        "name_zh": "万人医疗机构病床增长率",
        "unit": "%",
        "deps": ["medical_bed_num", "long_term_pop"],
        "expr": (
            "((medical_bed_num / long_term_pop)"
            " - (prev_medical_bed_num / prev_long_term_pop))"
            " / (prev_medical_bed_num / prev_long_term_pop) * 100"
        ),
        "needs_prev_year": True,
    },
    {
        "name_en": "patent_auth_100thousand",
        "name_zh": "十万人专利授权量",
        "unit": "件/十万人",
        "deps": ["grant_patent_num", "long_term_pop"],
        "expr": "grant_patent_num / long_term_pop * 10",
    },
    {
        "name_en": "culture_budget_expend_rate",
        "name_zh": "文化体育传媒经费占地方财政一般预算支出比重",
        "unit": "%",
        "deps": ["culture_budget_expend", "public_budget_expend"],
        "expr": "culture_budget_expend / public_budget_expend * 100",
    },
    {
        "name_en": "culture_space_num_100thousand",
        "name_zh": "十万人拥有文化场馆数量",
        "unit": "个/十万人",
        "deps": ["cultural_center_num", "museum_num", "library_num", "long_term_pop"],
        "expr": (
            "(cultural_center_num + museum_num + library_num)"
            " / long_term_pop * 10"
        ),
    },
    {
        "name_en": "art_team_num_100thousand",
        "name_zh": "十万人拥有艺术表演团体数量",
        "unit": "个/十万人",
        "deps": ["art_team_num", "long_term_pop"],
        "expr": "art_team_num / long_term_pop * 10",
    },
    {
        "name_en": "sport_center_num_100thousand",
        "name_zh": "十万人拥有体育场馆",
        "unit": "个/十万人",
        "deps": ["sport_center_num", "long_term_pop"],
        "expr": "sport_center_num / long_term_pop * 10",
    },
    {
        "name_en": "environment_budget_expend_rate",
        "name_zh": "环保资金支出占地方财政一般预算支出的比重",
        "unit": "%",
        "deps": ["environment_budget_expend", "public_budget_expend"],
        "expr": "environment_budget_expend / public_budget_expend * 100",
    },
    {
        "name_en": "so2_10thousand_gdp",
        "name_zh": "万元GDP二氧化硫排放量",
        "unit": "吨/万元",
        "deps": ["so2_total", "gdp"],
        "expr": "so2_total / (gdp * 10000)",
    },
    {
        "name_en": "so2_10thousand_gdp_decre_rate",
        "name_zh": "万元GDP二氧化硫排放量降低率",
        "unit": "%",
        "deps": ["so2_total", "gdp"],
        "expr": (
            "((prev_so2_total / (prev_gdp * 10000))"
            " - (so2_total / (gdp * 10000)))"
            " / (prev_so2_total / (prev_gdp * 10000)) * 100"
        ),
        "needs_prev_year": True,
    },
    {
        "name_en": "green_area_avg",
        "name_zh": "人均园林绿地面积",
        "unit": "平方米/人",
        "deps": ["green_area", "long_term_pop"],
        "expr": "green_area / long_term_pop",
    },
    {
        "name_en": "rural_urban_income_incre_rate_ratio",
        "name_zh": "农村家庭居民人均纯收入增长率与城镇家庭居民人均可支配性收入增长率之比",
        "unit": "比值",
        "deps": ["incre_rate_country_avg_income", "incre_rate_city_avg_income"],
        "expr": "incre_rate_country_avg_income / incre_rate_city_avg_income",
    },
    {
        "name_en": "country_income_in_city_income",
        "name_zh": "农村家庭居民人均纯收入绝对值与城镇家庭居民人均可支配收入绝对值之比",
        "unit": "比值",
        "deps": ["country_avg_income", "city_avg_income"],
        "expr": "country_avg_income / city_avg_income",
    },
    {
        "name_en": "country_expand_in_city_expand",
        "name_zh": "农村家庭人均生活消费支出与城镇家庭人均消费支出之比",
        "unit": "比值",
        "deps": ["country_avg_consumption_expend", "city_avg_consumption_expend"],
        "expr": "country_avg_consumption_expend / city_avg_consumption_expend",
    },
    {
        "name_en": "extreme_diff_index_avg_gdp_regions",
        "name_zh": "区域间人均GDP极值差距指数",
        "unit": "指数",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "extreme_diff_index_avg_income_regions",
        "name_zh": "区域间人均一般预算收入极值差距指数",
        "unit": "指数",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "extreme_diff_index_city_income_regions",
        "name_zh": "区域间城乡收入极值差距指数",
        "unit": "指数",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "avg_civil_servant_gdp",
        "name_zh": "公务员对GDP的人均贡献率",
        "unit": "万元/人",
        "deps": ["gdp", "work_pop_government_agency"],
        "expr": "gdp * 10000 / work_pop_government_agency",
    },
    {
        "name_en": "per_civil_servant_serve_pop",
        "name_zh": "单位公务员服务的人口数",
        "unit": "人",
        "deps": ["long_term_pop", "work_pop_government_agency"],
        "expr": "long_term_pop * 10000 / work_pop_government_agency",
    },
    {
        "name_en": "avg_finance_expend_gdp",
        "name_zh": "单位财政支出对GDP的贡献率",
        "unit": "比值",
        "deps": ["gdp", "public_budget_expend"],
        "expr": "gdp / public_budget_expend",
    },
    {
        "name_en": "complaint_case_100thousand",
        "name_zh": "十万人信访举报率",
        "unit": "件/十万人",
        "deps": ["complaint_case_num", "long_term_pop"],
        "expr": "complaint_case_num / long_term_pop * 10",
    },
    {
        "name_en": "civil_servant_crime_rate",
        "name_zh": "国家公务员职务犯罪率",
        "unit": "%",
        "deps": [
            "corruption_bribery_num",
            "dereliction_duty_num",
            "work_pop_government_agency",
        ],
        "expr": (
            "(corruption_bribery_num + dereliction_duty_num)"
            " / work_pop_government_agency * 100"
        ),
    },
    {
        "name_en": "admin_budget_expend_rate",
        "name_zh": "行政管理支出占财政支出的比重",
        "unit": "%",
        "deps": ["public_service_budget_expend", "public_budget_expend"],
        "expr": "public_service_budget_expend / public_budget_expend * 100",
    },
    {
        "name_en": "admin_gdp_elasticity_coefficient",
        "name_zh": "行政管理支出相对于GDP的弹性系数",
        "unit": "系数",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "admin_finance_expend_elasticity_coefficient",
        "name_zh": "行政管理支出相对于财政支出的弹性系数",
        "unit": "系数",
        "deps": [],
        "expr": None,
    },
    {
        "name_en": "admin_staff_rate",
        "name_zh": "机关单位就业人员占全体就业人员的比重",
        "unit": "%",
        "deps": ["work_pop_government_agency", "social_employment_pop"],
        "expr": "work_pop_government_agency / (social_employment_pop * 10000) * 100",
    },
    {
        "name_en": "incre_rate_active_disclose_government_information",
        "name_zh": "主动公开政府信息增长率",
        "unit": "%",
        "deps": ["active_disclose_government_information_num"],
        "expr": (
            "(active_disclose_government_information_num"
            " - prev_active_disclose_government_information_num)"
            " / prev_active_disclose_government_information_num * 100"
        ),
        "needs_prev_year": True,
    },
    {
        "name_en": "incre_rate_apply_disclose_government_information",
        "name_zh": "依申请公开政府信息增长率",
        "unit": "%",
        "deps": ["apply_disclose_government_information_num"],
        "expr": (
            "(apply_disclose_government_information_num"
            " - prev_apply_disclose_government_information_num)"
            " / prev_apply_disclose_government_information_num * 100"
        ),
        "needs_prev_year": True,
    },
]


def get_calc_indicator_map() -> dict[str, CalcIndicator]:
    return {item["name_en"]: item for item in CALC_INDICATORS}


def get_calc_name_en_set() -> set[str]:
    return {item["name_en"] for item in CALC_INDICATORS}


def get_calc_name_zh_set() -> set[str]:
    return {item["name_zh"] for item in CALC_INDICATORS}


def get_calc_indimap_entries() -> dict[str, str]:
    """中文名 → name_en，供注册进 INDIMAP。"""
    return {item["name_zh"]: item["name_en"] for item in CALC_INDICATORS}


def get_calc_indimap_unit_entries() -> dict[str, dict[str, str]]:
    """name_en → {unit, name_zh}，供注册进 INDIMAP_UNIT。"""
    return {
        item["name_en"]: {"unit": item["unit"], "name_zh": item["name_zh"]}
        for item in CALC_INDICATORS
    }


def is_calc_indicator_zh(name_zh: str) -> bool:
    return name_zh in get_calc_name_zh_set()


def is_calc_indicator_en(name_en: str) -> bool:
    return name_en in get_calc_name_en_set()
