# Generated by Django 4.1.6 on 2023-05-12 18:26

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('variant', models.CharField(choices=[('POS', 'Positive'), ('NEG', 'Negative'), ('IGN', 'Ignore')], default='NEG', max_length=3)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('description', models.CharField(max_length=512)),
                ('account', models.CharField(max_length=255)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('amount', models.IntegerField()),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='transaction_log_set', to='api.category')),
            ],
            managers=[
                ('admin_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='TransactionMerge',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.PositiveIntegerField()),
                ('from_transaction', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='frommerge', to='api.transaction')),
                ('to_transaction', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='tomerge', to='api.transaction')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CategoryMatcher',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('regex_expression', models.CharField(max_length=255, unique=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='category_matcher_set', to='api.category')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['date', 'description', 'account', 'amount'], name='api_transac_date_ff019d_idx'),
        ),
    ]
