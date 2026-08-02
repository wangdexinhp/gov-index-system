from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0011_indicator_input_method"),
    ]

    operations = [
        migrations.AlterField(
            model_name="indicatorcoveragestats",
            name="indicator_name_en",
            field=models.CharField(max_length=128, verbose_name="指标英文代码"),
        ),
    ]
