# Generated by Django 4.0 on 2022-11-16 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0003_order_delivery_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery_company',
            field=models.CharField(blank=True, choices=[('DPD', 'Dpd'), ('Fedex', 'Fedex'), ('UPS', 'Ups')], max_length=20, null=True),
        ),
    ]
