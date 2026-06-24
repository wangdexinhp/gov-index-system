from django.db import migrations, models


def migrate_legacy_input_source(apps, schema_editor):
    """历史数据：source='INPUT' 表示误存的手工录入，迁到 input_method。"""
    for model_name in ("Indicator", "IndicatorArea"):
        Model = apps.get_model("coredata", model_name)
        Model.objects.filter(source="INPUT").update(
            input_method="MANUAL",
            source="",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0010_order_alipay_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="indicator",
            name="input_method",
            field=models.CharField(
                blank=True,
                choices=[("MANUAL", "手工录入"), ("EXCEL", "Excel录入")],
                default="MANUAL",
                help_text="手工录入或 Excel 批量导入",
                max_length=16,
                verbose_name="录入方式",
            ),
        ),
        migrations.AddField(
            model_name="indicatorarea",
            name="input_method",
            field=models.CharField(
                blank=True,
                choices=[("MANUAL", "手工录入"), ("EXCEL", "Excel录入")],
                default="MANUAL",
                help_text="手工录入或 Excel 批量导入",
                max_length=16,
                verbose_name="录入方式",
            ),
        ),
        migrations.AlterField(
            model_name="indicator",
            name="source",
            field=models.CharField(
                blank=True,
                default="",
                help_text="指标数据来源类别或具体名称",
                max_length=50,
                verbose_name="数据来源",
            ),
        ),
        migrations.AlterField(
            model_name="indicatorarea",
            name="source",
            field=models.CharField(
                blank=True,
                default="",
                help_text="指标数据来源类别或具体名称",
                max_length=50,
                verbose_name="数据来源",
            ),
        ),
        migrations.RunPython(migrate_legacy_input_source, migrations.RunPython.noop),
    ]
