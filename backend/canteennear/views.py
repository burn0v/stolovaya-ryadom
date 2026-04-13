import requests
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.db.models import Exists, OuterRef
from django.urls import reverse
from .models import Canteen, Review
from .forms import UserRegisterForm
from django.contrib import messages
from geopy.distance import geodesic

def _catalog_api_key():
    return getattr(settings, "TWO_GIS_MAP_KEY", "")

def home(request):
    canteens = Canteen.objects.all()[:6]
    return render(request, "home.html", {"canteens": canteens})

def search(request):
    query = request.GET.get("q", "").strip()
    user_lat, user_lng = None, None
    
    if query:
        # Геокодируем адрес через 2GIS
        geo_url = (
            f"https://catalog.api.2gis.com/3.0/items/geocode?q=Казань, {query}"
            f"&fields=items.point&key={_catalog_api_key()}"
        )
        try:
            res = requests.get(geo_url).json()
            point = res['result']['items'][0]['point']
            user_lat, user_lng = point['lat'], point['lon']
            
            # Подгружаем новые места из 2GIS в базу
            fetch_2gis_orgs(user_lat, user_lng)
        except:
            pass

    all_canteens = (
        Canteen.objects.exclude(lat__isnull=True)
        .exclude(lng__isnull=True)
    )
    filtered_canteens = []

    if user_lat:
        for c in all_canteens:
            dist = geodesic((user_lat, user_lng), (c.lat, c.lng)).meters
            if dist <= 1500:
                c.distance = int(dist)
                filtered_canteens.append(c)
        filtered_canteens.sort(key=lambda x: x.distance)
    else:
        filtered_canteens = all_canteens.order_by('-rating')[:10]

    map_markers = [
        {
            "id": c.id,
            "lat": float(c.lat),
            "lng": float(c.lng),
            "name": c.name,
            "address": c.address,
            "detail_url": reverse("canteen_detail", kwargs={"id": c.id}),
        }
        for c in all_canteens
    ]
    map_options = {
        "center_lat": float(user_lat) if user_lat is not None else 55.7961,
        "center_lng": float(user_lng) if user_lng is not None else 49.1064,
        "user_lat": float(user_lat) if user_lat is not None else None,
        "user_lng": float(user_lng) if user_lng is not None else None,
    }

    return render(request, "search.html", {
        "all_canteens": all_canteens,
        "filtered_canteens": filtered_canteens,
        "query": query,
        "user_lat": user_lat,
        "user_lng": user_lng,
        "gis_map_key": settings.TWO_GIS_MAP_KEY,
        "map_markers": map_markers,
        "map_options": map_options,
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

            url = reverse("canteen_detail", kwargs={"id": canteen.id})
            if request.GET.get("from") == "reviews":
                url = f"{url}?from=reviews"
            return redirect(url)

    hide_map = request.GET.get("from") == "reviews"
    show_detail_map = bool(
        canteen.lat is not None and canteen.lng is not None and not hide_map
    )

    return render(request, "canteen_detail.html", {
        "canteen": canteen,
        "reviews": reviews,
        "hide_map": hide_map,
        "show_detail_map": show_detail_map,
        "gis_map_key": settings.TWO_GIS_MAP_KEY,
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


# Запросы к 2GIS Catalog API: отдельный поисковый запрос на каждый тип заведения,
# затем объединение результатов (параметр `q` задаёт текстовый поиск по рубрикам/названиям).
FOOD_PLACE_QUERIES = (
    "столовая",
    "кафе",
    "ресторан",
    "бар",
    "пиццерия",
    "кофейня",
    "фастфуд",
    "стейк-хаус",
)


class EstablishmentsWithReviewsView(ListView):
    """Заведения, у которых есть хотя бы один отзыв."""
    model = Canteen
    template_name = "reviews_list.html"
    context_object_name = "canteens"

    def get_queryset(self):
        return (
            Canteen.objects.filter(Exists(Review.objects.filter(canteen_id=OuterRef("pk"))))
            .order_by("-rating", "name")
        )


def fetch_2gis_orgs(lat, lng):
    """Подгружаем заведения общепита из 2GIS вокруг точки (несколько поисковых запросов)."""
    url = "https://catalog.api.2gis.com/3.0/items"
    base_params = {
        "point": f"{lng},{lat}",
        "radius": 1000,
        "fields": "items.point,items.address_name,items.schedule",
        "key": _catalog_api_key(),
    }
    for q in FOOD_PLACE_QUERIES:
        params = {**base_params, "q": q}
        try:
            res = requests.get(url, params=params, timeout=10).json()
            for item in res.get("result", {}).get("items", []):
                name = item.get("name")
                address = item.get("address_name", "Адрес не указан")
                point = item.get("point") or {}
                plat, plng = point.get("lat"), point.get("lon")
                if plat is None or plng is None:
                    continue
                if not Canteen.objects.filter(lat=plat, lng=plng).exists():
                    Canteen.objects.create(
                        name=name,
                        address=address,
                        lat=plat,
                        lng=plng,
                    )
        except Exception:
            continue