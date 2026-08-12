from django.core.management.base import BaseCommand
from django.db.models import Min

from apps.coredata.models.indicator import Indicator
from apps.coredata.services.formula_engine import recompute_for_city_years


class Command(BaseCommand):
    help = "按已有录入数据批量回算计算型指标（input_form=CALC）"

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, help="仅回算指定年份")
        parser.add_argument(
            "--city-id",
            type=int,
            dest="city_id",
            help="仅回算指定 city_id",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="只统计将处理的城市×年份数量，不写库",
        )

    def handle(self, *args, **options):
        qs = (
            Indicator.objects.exclude(city_id=0)
            .exclude(year__isnull=True)
            .values("city_id", "year")
            .annotate(province_id=Min("province_id"))
            .order_by("year", "city_id")
        )
        year = options.get("year")
        city_id = options.get("city_id")
        if year:
            qs = qs.filter(year=year)
        if city_id:
            qs = qs.filter(city_id=city_id)

        pairs = [
            (int(row["city_id"]), int(row["year"]), int(row["province_id"] or 0))
            for row in qs
        ]
        self.stdout.write(f"待回算城市×年份: {len(pairs)}")
        if options.get("dry_run"):
            return
        if not pairs:
            self.stdout.write(self.style.WARNING("无数据可回算"))
            return

        total = 0
        batch = 50
        for i in range(0, len(pairs), batch):
            chunk = pairs[i : i + batch]
            n = recompute_for_city_years(chunk)
            total += n
            self.stdout.write(
                f"进度 {min(i + batch, len(pairs))}/{len(pairs)}，本批写入 {n}，累计 {total}"
            )
        self.stdout.write(self.style.SUCCESS(f"回算完成，合计写入 {total} 条计算指标"))
