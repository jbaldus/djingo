# Generated by Django 5.1.6 on 2025-03-02 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0002_bingoboarditem_approved_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bingoboarditem',
            name='suggested_by',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
    ]
