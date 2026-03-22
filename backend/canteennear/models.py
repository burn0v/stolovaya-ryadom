from django.db import models

class Canteen(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    rating = models.FloatField(default=0)

    working_hours = models.CharField(
        max_length=200,
        default="Время работы не указано"
        )
    menu = models.TextField(default="Меню пока не добавлено")

    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)


    def __str__(self):
        return self.name
