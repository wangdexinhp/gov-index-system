# dashboard/management/commands/init_pricing_data.py
from django.core.management.base import BaseCommand
from dashboard.models import PricingConfig, IndicatorConfig, DurationMultiplierConfig


class Command(BaseCommand):
    help = '初始化定价配置数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化价格配置数据...')
        
        # ==================== 清空现有指标数据 ====================
        IndicatorConfig.objects.all().delete()
        self.stdout.write('已清空现有指标数据')
        
        # ==================== 价格配置数据（保持不变） ====================
        pricing_data = [
            # 全国级别
            ('全国', 'national', 'personal', '个人用户', 'year', '年', 19999.00, 365, 10),
            ('全国', 'national', 'org', '机构用户', 'year', '年', 29999.00, 365, 11),
            ('全国', 'national', 'personal', 'month', '月', 1999.00, 30, 12),
            ('全国', 'national', 'org', 'month', '月', 2999.00, 30, 13),
            ('全国', 'national', 'personal', '15days', '15天', 1199.00, 15, 14),
            ('全国', 'national', 'org', '15days', '15天', 1799.00, 15, 15),
            
            # 地区级别
            ('地区', 'region', 'personal', '个人用户', 'year', '年', 7999.00, 365, 20),
            ('地区', 'region', 'org', '机构用户', 'year', '年', 9999.00, 365, 21),
            ('地区', 'region', 'personal', 'month', '月', 799.00, 30, 22),
            ('地区', 'region', 'org', 'month', '月', 999.00, 30, 23),
            
            # 省份级别
            ('省', 'province', 'personal', '个人用户', 'year', '年', 2999.00, 365, 30),
            ('省', 'province', 'org', '机构用户', 'year', '年', 3999.00, 365, 31),
            ('省', 'province', 'personal', 'month', '月', 299.00, 30, 32),
            ('省', 'province', 'org', 'month', '月', 399.00, 30, 33),
            ('省', 'province', 'personal', 'week', '周', 149.00, 7, 34),
            ('省', 'province', 'org', 'week', '周', 199.00, 7, 35),
            ('省', 'province', 'personal', '24hour', '24小时', 59.00, 1, 36),
            ('省', 'province', 'org', '24hour', '24小时', 79.00, 1, 37),
            
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
                self.stdout.write(f'  创建价格配置: {obj}')
        
        # ==================== 个人用户指标（无，全部为空） ====================
        # 个人用户不配置任何指标（保持为空列表）
        self.stdout.write('个人用户指标: 无（空列表）')
        
        # ==================== 机构用户指标（仅以下指标） ====================
        org_indicators = [
            # 财政类
            ('一般公共预算支出', '财政支出数据', 10),
            ('一般公共服务支出', '公共服务财政支出', 20),
            ('科学技术支出', '科技领域财政支出', 30),
            ('文化体育传媒支出', '文化体育传媒财政支出', 40),
            ('环保支出', '环境保护财政支出', 50),
            ('社会保障和就业支出', '社保就业财政支出', 60),
            ('教育支出', '教育领域财政支出', 70),
            ('医疗卫生支出', '医疗卫生财政支出', 80),
            
            # 就业类
            ('采矿（掘)业就业人员人数', '采矿业就业人员', 90),
            ('制造业就业人员人数', '制造业就业人员', 100),
            ('城镇单位职工工资总额', '城镇单位职工工资总额', 110),
            ('城镇就业人数（城镇单位职工总数）', '城镇就业人数统计', 120),
            ('社会从业人员', '社会从业人员总数', 130),
            ('城镇登记失业人员数', '城镇登记失业人数', 140),
            
            # 经济类
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
            
            # 国有资产类
            ('国有资产保值增值率', '国有资产保值增值', 280),
            
            # 公共安全类
            ('公共安全支出', '公共安全财政支出', 290),
            
            # 政务公开类
            ('依申请公开政府信息件数', '依申请公开信息数量', 300),
            
            # 社会保障类
            ('城镇最低生活保障人数', '城镇低保人数', 310),
            ('农村最低生活保障人数', '农村低保人数', 320),
            
            # 人口类
            ('出生人口性别比', '出生性别比例', 330),
            ('人口出生率', '人口出生率', 340),
            
            # 工资类
            ('机关单位工资总额', '机关单位工资总额', 350),
            ('公共管理、社会保障和社会组织工资总额', '公共管理社保组织工资总额', 360),
            ('公共管理、社会保障和社会组织在岗职工人数', '公共管理社保组织在岗职工数', 370),
        ]
        
        for name, desc, sort_order in org_indicators:
            obj = IndicatorConfig.objects.create(
                user_type='org',
                user_type_name='机构用户',
                indicator_name=name,
                indicator_desc=desc,
                sort_order=sort_order,
                is_active=True
            )
            self.stdout.write(f'  创建机构指标: {obj}')
        
        self.stdout.write(f'机构用户指标数量: {len(org_indicators)} 项')
        
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
                self.stdout.write(f'  创建时长系数: {obj}')
        
        self.stdout.write(self.style.SUCCESS('价格配置数据初始化完成！'))
        self.stdout.write(self.style.SUCCESS(f'机构指标共计: {len(org_indicators)} 项'))
        self.stdout.write(self.style.WARNING('个人指标: 无（空列表）'))