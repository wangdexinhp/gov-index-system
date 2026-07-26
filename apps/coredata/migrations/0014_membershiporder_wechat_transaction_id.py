from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coredata", "0013_source_text_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="membershiporder",
            name="wechat_transaction_id",
            field=models.CharField("微信交易号", max_length=64, blank=True, default=""),
        ),
    ]
