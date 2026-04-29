
from django.core.management.base import BaseCommand
from apps.coredata.models.price import PricingConfig, IndicatorConfig, DurationMultiplierConfig


class Command(BaseCommand):
    help = '初始化定价配置数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化配置数据...')
        
        # ==================== 清空现有指标数据 ====================
        IndicatorConfig.objects.all().delete()
        self.stdout.write('已清空现有指标数据')
        
        # ==================== 价格配置数据 ====================
        # 格式: (level, level_code, user_type, user_type_name, duration, duration_name, price, days, sort_order)
        pricing_data = [
            # 全国级别
            ('全国', 'national', 'personal', '个人用户', 'year', '年', 19999.00, 365, 10),
            ('全国', 'national', 'org', '机构用户', 'year', '年', 29999.00, 365, 11),
            ('全国', 'national', 'personal', '个人用户', 'month', '月', 1999.00, 30, 12),
            ('全国', 'national', 'org', '机构用户', 'month', '月', 2999.00, 30, 13),
            ('全国', 'national', 'personal', '个人用户', '15days', '15天', 1199.00, 15, 14),
            ('全国', 'national', 'org', '机构用户', '15days', '15天', 1799.00, 15, 15),
            
            # 地区级别
            ('地区', 'region', 'personal', '个人用户', 'year', '年', 7999.00, 365, 20),
            ('地区', 'region', 'org', '机构用户', 'year', '年', 9999.00, 365, 21),
            ('地区', 'region', 'personal', '个人用户', 'month', '月', 799.00, 30, 22),
            ('地区', 'region', 'org', '机构用户', 'month', '月', 999.00, 30, 23),
            
            # 省份级别
            ('省', 'province', 'personal', '个人用户', 'year', '年', 2999.00, 365, 30),
            ('省', 'province', 'org', '机构用户', 'year', '年', 3999.00, 365, 31),
            ('省', 'province', 'personal', '个人用户', 'month', '月', 299.00, 30, 32),
            ('省', 'province', 'org', '机构用户', 'month', '月', 399.00, 30, 33),
            ('省', 'province', 'personal', '个人用户', 'week', '周', 149.00, 7, 34),
            ('省', 'province', 'org', '机构用户', 'week', '周', 199.00, 7, 35),
            ('省', 'province', 'personal', '个人用户', '24hour', '24小时', 59.00, 1, 36),
            ('省', 'province', 'org', '机构用户', '24hour', '24小时', 79.00, 1, 37),
            
            # 直辖市级别
            ('直辖市', 'municipality', 'personal', '个人用户', '24hour', '24小时', 49.00, 1, 40),
            ('直辖市', 'municipality', 'org', '机构用户', '24hour', '24小时', 69.00, 1, 41),
            
            # 城市级别
            ('市', 'city', 'personal', '个人用户', '24hour', '24小时', 29.00, 1, 50),
            ('市', 'city', 'org', '机构用户', '24hour', '24小时', 49.00, 1, 51),
        ]
        
        for data in pricing_data:
            obj, created = PricingConfig.objects.get_or_create(
                level_code=data[1],
                user_type=data[2],
                duration=data[4],
                defaults={
                    'level': data[0],
                    'user_type_name': data[3],
                    'duration_name': data[5],
                    'price': data[6],
                    'days': data[7],
                    'sort_order': data[8],
                }
            )
            if created:
                self.stdout.write(f'  创建价格配置: {obj.level}-{obj.user_type_name}-{obj.duration_name}')
        
        # ==================== 机构用户指标 ====================
        org_indicators = [
            ('一般公共预算支出', '财政支出数据', 10),
            ('一般公共服务支出', '公共服务财政支出', 20),
            ('科学技术支出', '科技领域财政支出', 30),
            ('文化体育传媒支出', '文化体育传媒财政支出', 40),
            ('环保支出', '环境保护财政支出', 50),
            ('社会保障和就业支出', '社保就业财政支出', 60),
            ('教育支出', '教育领域财政支出', 70),
            ('医疗卫生支出', '医疗卫生财政支出', 80),
            ('采矿（掘)业就业人员人数', '采矿业就业人员', 90),
            ('制造业就业人员人数', '制造业就业人员', 100),
            ('城镇单位职工工资总额', '城镇单位职工工资总额', 110),
            ('城镇就业人数（城镇单位职工总数）', '城镇就业人数统计', 120),
            ('社会从业人员', '社会从业人员总数', 130),
            ('城镇登记失业人员数', '城镇登记失业人数', 140),
            ('财政总收入', '财政收入总额', 150),
            ('财政总收入增长率', '财政收入增长率', 160),
            ('固定资产投资总额', '固定资产投资总额', 170),
            ('固定资产投资总额增长率', '固定资产投资增长率', 180),
            ('进出口总额', '进出口贸易总额', 190),
            ('进出口总额增长率', '进出口贸易增长率', 200),
            ('实际利用外资金额', '实际利用外资', 210),
            ('实际利用外资金额增长率', '实际利用外资增长率', 220),
            ('规模以上工业企业增加值', '规上工业增加值', 230),
            ('第二产业增加值占GDP（增量）比重', '第二产业占比', 240),
            ('第三产业增加值占GDP（增量）比重', '第三产业占比', 250),
            ('能源消耗总量', '能源消耗总量', 260),
            ('万元GDP综合能源消耗', '万元GDP能耗', 270),
            ('国有资产保值增值率', '国有资产保值增值', 280),
            ('公共安全支出', '公共安全财政支出', 290),
            ('依申请公开政府信息件数', '依申请公开信息数量', 300),
            ('城镇最低生活保障人数', '城镇低保人数', 310),
            ('农村最低生活保障人数', '农村低保人数', 320),
            ('出生人口性别比', '出生性别比例', 330),
            ('人口出生率', '人口出生率', 340),
            ('机关单位工资总额', '机关单位工资总额', 350),
            ('公共管理、社会保障和社会组织工资总额', '公共管理社保组织工资总额', 360),
            ('公共管理、社会保障和社会组织在岗职工人数', '公共管理社保组织在岗职工数', 370),
        ]
        
        for name, desc, sort_order in org_indicators:
            # 先检查是否已存在，避免重复创建
            obj, created = IndicatorConfig.objects.get_or_create(
                user_type='org',
                indicator_name=name,
                defaults={
                    'user_type_name': '机构用户',
                    'indicator_desc': desc,
                    'sort_order': sort_order,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  创建机构指标: {obj.indicator_name}')
        
        self.stdout.write(f'机构用户指标数量: {IndicatorConfig.objects.filter(user_type="org").count()} 项')
        self.stdout.write('个人用户指标: 无（空列表）')
        
        # ==================== 时长系数配置数据 ====================
        duration_data = [
            ('year', '年卡', 1.0000, 10),
            ('month', '月卡', 0.1000, 20),
            ('week', '周卡', 0.0250, 30),
        ]
        
        for code, name, multiplier, sort_order in duration_data:
            obj, created = DurationMultiplierConfig.objects.get_or_create(
                duration_code=code,
                defaults={
                    'duration_name': name,
                    'multiplier': multiplier,
                    'sort_order': sort_order,
                }
            )
            if created:
                self.stdout.write(f'  创建时长系数: {obj.duration_name}')
        
        self.stdout.write(self.style.SUCCESS('配置数据初始化完成！'))
        self.stdout.write(self.style.SUCCESS(f'机构指标共计: {IndicatorConfig.objects.filter(user_type="org").count()} 项'))
        self.stdout.write(self.style.WARNING('个人指标: 无（空列表）'))





price_list =  [
    { level: "全国", userType: "个人用户", duration: "year", price: 19999, days: 365, pricePerDay: 54.79 },
    { level: "全国", userType: "机构用户", duration: "year", price: 29999, days: 365, pricePerDay: 82.19 },
    { level: "全国", userType: "个人用户", duration: "month", price: 1999, days: 30, pricePerDay: 66.63 },
    { level: "全国", userType: "机构用户", duration: "month", price: 2999, days: 30, pricePerDay: 99.97 },

    { level: "地区", userType: "个人用户", duration: "year", price: 7999, days: 365, pricePerDay: 21.92 },
    { level: "地区", userType: "机构用户", duration: "year", price: 9999, days: 365, pricePerDay: 27.39 },
    { level: "地区", userType: "个人用户", duration: "month", price: 799, days: 30, pricePerDay: 26.63 },
    { level: "地区", userType: "机构用户", duration: "month", price: 999, days: 30, pricePerDay: 33.30 },

    { level: "省", userType: "个人用户", duration: "year", price: 2999, days: 365, pricePerDay: 8.22 },
    { level: "省", userType: "机构用户", duration: "year", price: 3999, days: 365, pricePerDay: 10.96 },
    { level: "省", userType: "个人用户", duration: "month", price: 299, days: 30, pricePerDay: 9.97 },
    { level: "省", userType: "机构用户", duration: "month", price: 399, days: 30, pricePerDay: 13.30 },
    { level: "省", userType: "个人用户", duration: "week", price: 149, days: 7, pricePerDay: 21.29 },
    { level: "省", userType: "机构用户", duration: "week", price: 199, days: 7, pricePerDay: 28.43 },
    { level: "省", userType: "个人用户", duration: "day", price: 59, days: 1, pricePerDay: 59.00 },
    { level: "省", userType: "机构用户", duration: "day", price: 79, days: 1, pricePerDay: 79.00 },

    { level: "直辖市", userType: "个人用户", duration: "year", price: 2999, days: 365, pricePerDay: 8.22 },
    { level: "直辖市", userType: "机构用户", duration: "year", price: 3999, days: 365, pricePerDay: 10.96 },
    { level: "直辖市", userType: "个人用户", duration: "month", price: 299, days: 30, pricePerDay: 9.97 },
    { level: "直辖市", userType: "机构用户", duration: "month", price: 399, days: 30, pricePerDay: 13.30 },
    { level: "直辖市", userType: "个人用户", duration: "day", price: 49, days: 1, pricePerDay: 49.00 },
    { level: "直辖市", userType: "机构用户", duration: "day", price: 69, days: 1, pricePerDay: 69.00 },

    { level: "市", userType: "个人用户", duration: "year", price: 799, days: 365, pricePerDay: 2.19 },
    { level: "市", userType: "机构用户", duration: "year", price: 999, days: 365, pricePerDay: 2.74 },
    { level: "市", userType: "个人用户", duration: "month", price: 79, days: 30, pricePerDay: 2.63 },
    { level: "市", userType: "机构用户", duration: "month", price: 99, days: 30, pricePerDay: 3.30 },
    { level: "市", userType: "个人用户", duration: "day", price: 29, days: 1, pricePerDay: 29.00 },
    { level: "市", userType: "机构用户", duration: "day", price: 49, days: 1, pricePerDay: 49.00 }
];