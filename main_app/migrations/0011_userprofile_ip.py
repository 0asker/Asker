# Generated by Django 2.2.7 on 2021-04-18 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0010_userprofile_blocked_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='ip',
            field=models.TextField(null=True),
        ),
    ]
