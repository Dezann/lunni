# Generated by Django 4.1.6 on 2023-04-12 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merger', '0002_transactioncategory_transactioncategorymatcher_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactioncategory',
            name='variant',
            field=models.CharField(choices=[('POS', 'Positive'), ('NEG', 'Negative'), ('IGN', 'Ignore')], default='NEG', max_length=3),
        ),
    ]
