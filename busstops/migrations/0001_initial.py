# Generated by Django 5.1.4 on 2025-03-23 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BoardingPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1000)),
                ('province', models.CharField(blank=True, choices=[('Central Province', 'Central Province'), ('Eastern Province', 'Eastern Province'), ('North Central Province', 'North Central Province'), ('Northern Province', 'Northern Province'), ('North Western Province', 'North Western Province'), ('Sabaragamuwa Province', 'Sabaragamuwa Province'), ('Southern Province', 'Southern Province'), ('Uva Province', 'Uva Province'), ('Western Province', 'Western Province')], max_length=250)),
                ('city', models.CharField(blank=True, choices=[('Ampara District', 'Ampara District'), ('Anuradhapura District', 'Anuradhapura District'), ('Badulla District', 'Badulla District'), ('Batticaloa District', 'Batticaloa District'), ('Colombo District', 'Colombo District'), ('Galle District', 'Galle District'), ('Gampaha District', 'Gampaha District'), ('Hambantota District', 'Hambantota District'), ('Jaffna District', 'Jaffna District'), ('Kalutara District', 'Kalutara District'), ('Kandy District', 'Kandy District'), ('Kegalle District', 'Kegalle District'), ('Kilinochchi District', 'Kilinochchi District'), ('Kurunegala District', 'Kurunegala District'), ('Mannar District', 'Mannar District'), ('Matale District', 'Matale District'), ('Matara District', 'Matara District'), ('Monaragala District', 'Monaragala District'), ('Mullaitivu District', 'Mullaitivu District'), ('Nuwara Eliya District', 'Nuwara Eliya District'), ('Polonnaruwa District', 'Polonnaruwa District'), ('Puttalam District', 'Puttalam District'), ('Ratnapura District', 'Ratnapura District'), ('Trincomalee District', 'Trincomalee District'), ('Vavuniya District', 'Vavuniya District')], max_length=250)),
                ('latitude', models.FloatField(default=1)),
                ('longitude', models.FloatField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Buses',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bus_name', models.CharField(blank=True, max_length=255)),
                ('bus_number', models.CharField(max_length=25)),
                ('seat_count', models.PositiveIntegerField(choices=[(32, '32-seater'), (40, '40-seater'), (52, '52-seater'), (64, '64-seater')], default=32)),
                ('bus_type', models.CharField(choices=[('NORMAL', 'Normal'), ('SEMI_LUXURY', 'Semi-Luxury'), ('LUXURY', 'Luxury')], default='NORMAL', max_length=20)),
                ('route_permit_number', models.CharField(blank=True, max_length=100, null=True)),
                ('route_permit_image', models.ImageField(blank=True, null=True, upload_to='route_permits/')),
                ('is_approved', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='BusFareLuxury',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fare_number', models.PositiveSmallIntegerField()),
                ('fare_price', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='BusFareSemiLuxury',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fare_number', models.PositiveSmallIntegerField()),
                ('fare_price', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='BusRoute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('route_number', models.CharField(blank=True, max_length=255, null=True)),
                ('display_name', models.CharField(default='Colombo-Kandy', max_length=255)),
                ('is_it_reversed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seat_number', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('position', models.PositiveSmallIntegerField(default=1)),
                ('distance', models.DecimalField(blank=True, decimal_places=2, help_text='in KM s', max_digits=6, null=True)),
                ('time', models.DurationField(blank=True, help_text='Normal travel time', null=True)),
                ('busy_time', models.DurationField(blank=True, help_text='Travel time during busy hours', null=True)),
            ],
        ),
    ]
