from geopy.geocoders import Nominatim
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
        full_address = f"Казань, {self.address}"
        
        geolocator = Nominatim(user_agent="canteennear_app")
        try:
            location = geolocator.geocode(full_address)
            if location:
                self.lat = location.latitude
                self.lng = location.longitude
        except Exception as e:
            print(f"Ошибка автоматического геокодирования: {e}")
        
        # Вызываем стандартный метод сохранения
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