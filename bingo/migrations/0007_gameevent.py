# Generated by Django 5.1.6 on 2025-03-29 01:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0006_remove_player_unique_player_name_per_game'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='bingo.bingogame')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='bingo.player')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
