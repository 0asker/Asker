# Generated by Django 3.2 on 2021-07-22 16:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ban',
            fields=[
                ('ip', models.TextField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_anonymous', models.BooleanField(default=True)),
                ('multichoice', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='PollChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('votes', models.IntegerField(default=0)),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.poll')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('description', models.TextField(null=True)),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('total_likes', models.IntegerField(default=0, null=True)),
                ('total_responses', models.IntegerField(default=0)),
                ('total_views', models.IntegerField(default=0, null=True)),
                ('best_answer', models.IntegerField(blank=True, null=True)),
                ('reports', models.IntegerField(default=0, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SilencedUsers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expires', models.DateTimeField(default=django.utils.timezone.now)),
                ('silenced', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.TextField(null=True)),
                ('avatar', models.ImageField(blank=True, default='avatars/default-avatar.png', upload_to='')),
                ('bio', models.TextField(blank=True, max_length=400)),
                ('total_points', models.IntegerField(blank=True, default=0, null=True)),
                ('total_views', models.IntegerField(blank=True, default=0)),
                ('rank', models.IntegerField(blank=True, default=-1, null=True)),
                ('active', models.BooleanField(default=True)),
                ('verification_code', models.TextField(null=True)),
                ('hide_activity', models.BooleanField(default=True)),
                ('ban', models.BooleanField(default=False)),
                ('message', models.TextField(null=True)),
                ('blocked_users', models.ManyToManyField(blank=True, related_name='blocked_by', to=settings.AUTH_USER_MODEL)),
                ('silenced_users', models.ManyToManyField(blank=True, related_name='silenced_by', through='main_app.SilencedUsers', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='silencedusers',
            name='silencer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.userprofile'),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('total_likes', models.IntegerField(default=0)),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.userprofile')),
                ('likes', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.question')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.userprofile'),
        ),
        migrations.CreateModel(
            name='PollVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.pollchoice')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.poll')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='poll',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.question'),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.TextField()),
                ('text', models.TextField(null=True)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('read', models.BooleanField(default=False)),
                ('liker', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='l', to=settings.AUTH_USER_MODEL)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('response', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='r', to='main_app.response')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.response')),
            ],
        ),
    ]
