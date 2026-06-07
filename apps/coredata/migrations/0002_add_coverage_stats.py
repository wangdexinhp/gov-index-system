from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CityCompletionStats",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("city_id", models.IntegerField(db_index=True, verbose_name="城市ID")),
                ("city_name", models.CharField(max_length=50, verbose_name="城市名称")),
                ("province_id", models.IntegerField(blank=True, null=True, verbose_name="省份ID")),
                ("province_name", models.CharField(blank=True, default="", max_length=50, verbose_name="省份名称")),
                ("year", models.IntegerField(db_index=True, verbose_name="年份")),
                ("total_indicators", models.IntegerField(verbose_name="应录入指标总数")),
                ("completed_indicators", models.IntegerField(verbose_name="已录入指标数")),
                ("completion_rate", models.DecimalField(decimal_places=2, max_digits=5, verbose_name="完成率(%)")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "地市完成率统计",
                "verbose_name_plural": "地市完成率统计",
                "db_table": "city_completion_stats",
                "ordering": ["-completion_rate", "city_name"],
                "indexes": [
                    models.Index(fields=["year", "completion_rate"], name="idx_ccs_year_rate"),
                ],
                "unique_together": {("city_id", "year")},
            },
        ),
        migrations.CreateModel(
            name="IndicatorCoverageStats",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("indicator_name", models.CharField(max_length=100, verbose_name="指标名称")),
                ("indicator_name_en", models.CharField(max_length=50, verbose_name="指标英文代码")),
                ("indicator_group", models.CharField(blank=True, default="", max_length=50, verbose_name="指标组")),
                ("year", models.IntegerField(db_index=True, verbose_name="年份")),
                ("total_cities", models.IntegerField(verbose_name="应录入城市总数")),
                ("covered_cities", models.IntegerField(verbose_name="已录入城市数")),
                ("coverage_rate", models.DecimalField(decimal_places=2, max_digits=5, verbose_name="覆盖率(%)")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "指标覆盖率统计",
                "verbose_name_plural": "指标覆盖率统计",
                "db_table": "indicator_coverage_stats",
                "ordering": ["-coverage_rate", "indicator_name"],
                "indexes": [
                    models.Index(fields=["year", "coverage_rate"], name="idx_ics_year_rate"),
                    models.Index(fields=["indicator_group", "year"], name="idx_ics_group_year"),
                ],
                "unique_together": {("indicator_name", "year")},
            },
        ),
    ]
