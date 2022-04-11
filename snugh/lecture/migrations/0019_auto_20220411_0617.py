# Generated by Django 3.2.6 on 2022-04-11 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lecture', '0018_auto_20220329_1238'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='plan',
            name='recent_scroll',
        ),
        migrations.AlterUniqueTogether(
            name='planmajor',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='semester',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='semesterlecture',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='planmajor',
            constraint=models.UniqueConstraint(fields=('plan', 'major'), name='major already exists in major.'),
        ),
        migrations.AddConstraint(
            model_name='semester',
            constraint=models.UniqueConstraint(fields=('plan', 'year', 'semester'), name='semester already exists in plan.'),
        ),
        migrations.AddConstraint(
            model_name='semesterlecture',
            constraint=models.UniqueConstraint(fields=('semester', 'lecture'), name='lecture already exists in semester.'),
        ),
    ]
