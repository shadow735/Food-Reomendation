# Generated by Django 4.1.13 on 2024-03-27 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('s_no', models.AutoField(primary_key=True, serialize=False)),
                ('Name', models.CharField(max_length=20)),
                ('Email', models.EmailField(max_length=50)),
                ('Subject', models.CharField(max_length=50)),
                ('Message', models.TextField()),
                ('timeStamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='DRI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age', models.IntegerField()),
                ('weight', models.FloatField()),
                ('height', models.FloatField()),
                ('gender', models.CharField(max_length=10)),
                ('activity_level', models.CharField(max_length=20)),
                ('goal', models.CharField(max_length=10)),
                ('meal_type', models.CharField(max_length=20)),
                ('total_protein', models.FloatField()),
                ('total_fat', models.FloatField()),
                ('total_carbohydrates', models.FloatField()),
                ('calorie_intake', models.FloatField()),
                ('meal_protein', models.FloatField()),
                ('meal_fat', models.FloatField()),
                ('meal_carbohydrates', models.FloatField()),
                ('meal_calories', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Food',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default Food Name', max_length=100)),
                ('food_id', models.IntegerField(default=0)),
                ('meal_type', models.CharField(max_length=100)),
            ],
        ),
    ]
