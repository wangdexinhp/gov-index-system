from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_userprofile_membership_level"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="org_credit_code",
            field=models.CharField(
                blank=True, default="", max_length=32, verbose_name="统一社会信用代码"
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="org_name",
            field=models.CharField(
                blank=True, default="", max_length=200, verbose_name="单位名称"
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="org_verified_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="机构认证通过时间"
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="org_verify_message",
            field=models.CharField(
                blank=True, default="", max_length=255, verbose_name="机构认证说明"
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="org_verify_status",
            field=models.CharField(
                choices=[
                    ("pending", "未认证"),
                    ("verified", "已认证"),
                    ("failed", "认证失败"),
                ],
                default="pending",
                max_length=20,
                verbose_name="机构认证状态",
            ),
        ),
    ]
