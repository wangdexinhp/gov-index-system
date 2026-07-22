from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0012_alter_indicatorcoveragestats_indicator_name_en"),
    ]

    operations = [
        migrations.AlterField(
            model_name="indicator",
            name="source",
            field=models.CharField(
                blank=True,
                default="",
                help_text="指标数据来源具体名称（文字）",
                max_length=200,
                verbose_name="数据来源",
            ),
        ),
        migrations.AlterField(
            model_name="indicatorarea",
            name="source",
            field=models.CharField(
                blank=True,
                default="",
                help_text="指标数据来源具体名称（文字）",
                max_length=200,
                verbose_name="数据来源",
            ),
        ),
    ]
