from django.core.management.base import BaseCommand
from django.db import transaction

from apps.coredata.models.indicator import Indicator

from django.core.management.base import BaseCommand
'''
class Command(BaseCommand):
    help = "调试：验证 init_indicators 命令是否执行到这里"

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUG: 现在执行的是 apps.coredata.management.commands.init_indicators 里的代码 ===")
'''
# 这里维护要导入的全部指标
INDICATORS_DATA = [
    {
        "name_en": "pm25",
        "name_zh": "PM2.5年均浓度",
        "input_form": "INPUT",  # 直接用枚举 value
        "indicator_type": "ENV",
    },
    {
        "name_en": "pm10",
        "name_zh": "PM10年均浓度",
        "input_form": "INPUT",
        "indicator_type": "ENV",
    },
    {
        "name_en": "gdp",
        "name_zh": "地区生产总值",
        "input_form": "INPUT",
        "indicator_type": "ECO",
    },
    {
        "name_en": "gdp_per_capita",
        "name_zh": "人均地区生产总值",
        "input_form": "CALC",
        "indicator_type": "ECO",
    },
]


class Command(BaseCommand):
    help = "初始化/更新所有指标数据到 Indicator 表中"

    def handle(self, *args, **options):
        if not INDICATORS_DATA:
            self.stdout.write(self.style.WARNING("INDICATORS_DATA 为空，没有任何指标被导入。"))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("正在初始化指标数据..."))

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for item in INDICATORS_DATA:
                name_en = item["name_en"]
                name_zh = item["name_zh"]
                input_form = item["input_form"]
                indicator_type = item["indicator_type"]

                obj, created = Indicator.objects.update_or_create(
                    name_en=name_en,
                    defaults={
                        "name_zh": name_zh,
                        "input_form": input_form,
                        "indicator_type": indicator_type,
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"  创建指标: {obj.name_en} - {obj.name_zh}")
                else:
                    updated_count += 1
                    self.stdout.write(f"  更新指标: {obj.name_en} - {obj.name_zh}")

        self.stdout.write(
            self.style.SUCCESS(
                f"指标数据初始化完成：新增 {created_count} 条，更新 {updated_count} 条。"
            )
        )
