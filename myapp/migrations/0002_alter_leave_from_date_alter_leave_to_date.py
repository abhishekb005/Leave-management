# Generated by Django 4.0.2 on 2022-02-19 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leave',
            name='from_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='leave',
            name='to_date',
            field=models.DateField(),
        ),
    ]
