# Generated by Django 4.2.7 on 2024-12-22 23:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("unclebudget", "0006_entry_expected_item_expected"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="item",
            name="expected",
        ),
    ]