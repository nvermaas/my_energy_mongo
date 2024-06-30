# Generated by Django 2.1.5 on 2019-02-10 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EnergyRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(null=True)),
                ('received_tariff1', models.FloatField(null=True)),
                ('received_tariff2', models.FloatField(null=True)),
                ('received_actual', models.FloatField(null=True)),
                ('delivered_tariff1', models.FloatField(null=True)),
                ('delivered_tariff2', models.FloatField(null=True)),
                ('delivered_actual', models.FloatField(null=True)),
                ('gas', models.FloatField(null=True)),
            ],
        ),
    ]
