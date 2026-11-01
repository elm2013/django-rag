from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('path', models.CharField(max_length=1024, unique=True)),
                ('sha256', models.CharField(blank=True, max_length=64)),
                ('chunk_count', models.PositiveIntegerField(default=0)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pending'),
                            ('indexed', 'Indexed'),
                            ('failed', 'Failed'),
                        ],
                        default='pending',
                        max_length=16,
                    ),
                ),
                (
                    'last_indexed_at',
                    models.DateTimeField(blank=True, null=True),
                ),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['path']},
        ),
    ]
