from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.shortcuts import render, get_object_or_404, redirect
from .models import Canteen, Review
from django.db.models import Q
from .forms import UserRegisterForm
from django.contrib import messages

def home(request):
    canteens = Canteen.objects.all()[:6]
    return render(request, "home.html", {"canteens": canteens})

def search(request):
    query = request.GET.get("q", "").strip()
    city_prefix = "Казань, " 
    
    # 1. Получаем ВООБЩЕ ВСЕ заведения с координатами для карты
    all_canteens = Canteen.objects.exclude(lat__isnull=True, lng__isnull=True)
    
    filtered_canteens = []
    user_lat = None
    user_lng = None
    search_type = None

    if query:
        # Пытаемся найти по названию
        by_name = Canteen.objects.filter(
            Q(name__icontains=query) | Q(address__icontains=query)
        )
        
        if by_name.exists():
            filtered_canteens = by_name.order_by('-rating')[:5]
        else:
            # Геокодируем адрес пользователя
            geolocator = Nominatim(user_agent="canteennear_app")
            try:
                location = geolocator.geocode(city_prefix + query)
                if location:
                    user_lat = location.latitude
                    user_lng = location.longitude
                    search_type = "radius"
                    user_coords = (user_lat, user_lng)
                    
                    # Ищем заведения в радиусе 800м для СПИСКА
                    temp_list = []
                    for c in all_canteens:
                        dist = geodesic(user_coords, (c.lat, c.lng)).meters
                        if dist <= 800:
                            c.distance = int(dist)
                            temp_list.append(c)
                    
                    # Сортируем по рейтингу и берем топ-5 для карточек
                    temp_list.sort(key=lambda x: x.rating, reverse=True)
                    filtered_canteens = temp_list[:5]
            except Exception as e:
                print(f"Geocode error: {e}")
    else:
        # Если поиска нет, в списке просто топ-5 по рейтингу
        filtered_canteens = all_canteens.order_by('-rating')[:5]

    return render(request, "search.html", {
        "all_canteens": all_canteens,         # Все точки для карты
        "filtered_canteens": filtered_canteens, # 5 карточек для списка
        "query": query, 
        "user_lat": user_lat,
        "user_lng": user_lng,
        "search_type": search_type
    })

def canteen_detail(request, id):
    canteen = get_object_or_404(Canteen, id=id)
    reviews = canteen.reviews.all().order_by('-created_at')
    
    if request.method == "POST" and request.user.is_authenticated:
        text = request.POST.get("text", "").strip()
        rating = request.POST.get("rating", "5")
        
        # Базовая защита: текст не пустой, рейтинг от 1 до 5
        if text and rating.isdigit() and 1 <= int(rating) <= 5:
            # 1. Создаем и сохраняем отзыв
            Review.objects.create(
                canteen=canteen,
                user=request.user,
                text=text[:1000],
                rating=int(rating)
            )
            # 2. Мгновенно обновляем рейтинг столовой
            canteen.update_rating()
            
            return redirect('canteen_detail', id=canteen.id)

    return render(request, "canteen_detail.html", {
        "canteen": canteen, 
        "reviews": reviews
    })

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})