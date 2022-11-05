# Generated by Django 4.0.6 on 2022-11-05 00:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unclebudget', '0006_alter_entry_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipt',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=9),
            preserve_default=False,
        ),
    ]
