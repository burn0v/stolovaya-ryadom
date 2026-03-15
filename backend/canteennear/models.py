from django.db import models

class Canteen(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    rating = models.FloatField(default=0)

    def __str__(self):
        return self.name
