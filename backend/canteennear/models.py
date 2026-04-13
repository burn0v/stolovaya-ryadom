import requests
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

class Canteen(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    rating = models.FloatField(default=0)
    working_hours = models.CharField(max_length=200, default="Время работы не указано")
    menu = models.TextField(default="Меню пока не добавлено")
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Авто-поиск координат через 2GIS Geocoding
        if not self.lat or not self.lng:
            api_key = getattr(settings, "TWO_GIS_MAP_KEY", "")
            # Ищем координаты по адресу в Казани
            url = f"https://catalog.api.2gis.com/3.0/items/geocode?q=Казань, {self.address}&fields=items.point&key={api_key}"
            try:
                res = requests.get(url).json()
                point = res['result']['items'][0]['point']
                self.lat = point['lat']
                self.lng = point['lon']
            except:
                pass 
        super().save(*args, **kwargs)

    def update_rating(self):
        # Вычисляем среднюю оценку по всем отзывам этой столовой
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        # Если отзывы есть, округляем до 1 знака. Если нет — ставим 0
        self.rating = round(avg_rating, 1) if avg_rating else 0
        self.save()

    def __str__(self):
        return self.name


class Review(models.Model):
    canteen = models.ForeignKey(Canteen, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.canteen.name}"