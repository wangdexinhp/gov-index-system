from django.core.management.base import BaseCommand

from apps.coredata.models.stats import CityCompletionStats, IndicatorCoverageStats
from apps.coredata.services.coverage_service import rebuild_coverage_stats


class Command(BaseCommand):
    help = "重建地市完成率与指标覆盖率统计表（city_completion_stats / indicator_coverage_stats）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            help="仅统计指定年份，例如 --year 2026",
        )
        parser.add_argument(
            "--years",
            type=str,
            help="统计多个年份，逗号分隔，例如 --years 2024,2025,2026",
        )

    def handle(self, *args, **options):
        year = options.get("year")
        years_str = options.get("years")

        if year and years_str:
            self.stderr.write(self.style.ERROR("--year 与 --years 不能同时使用"))
            return

        years = None
        if years_str:
            years = [int(y.strip()) for y in years_str.split(",") if y.strip()]

        self.stdout.write("开始重建覆盖统计表...")
        result = rebuild_coverage_stats(
            year_param=str(year) if year else None,
            years=years,
        )

        for y in result["years"]:
            city_count = CityCompletionStats.objects.filter(year=y).count()
            indicator_count = IndicatorCoverageStats.objects.filter(year=y).count()
            self.stdout.write(
                f"  {y} 年: 地市 {city_count} 条, 指标 {indicator_count} 条"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"完成！共重建 {result['rebuilt_count']} 个年份: {result['years']}"
            )
        )
