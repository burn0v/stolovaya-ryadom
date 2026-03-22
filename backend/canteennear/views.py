from django.shortcuts import render, get_object_or_404
from .models import Canteen
from django.db.models import Q

def home(request):
    # Берем последние 6 столовых для главной страницы
    canteens = Canteen.objects.all()[:6]
    return render(request, "home.html", {"canteens": canteens})

def search(request):
    query = request.GET.get("q", "").strip()
    # ВАЖНО: Определяем префикс города здесь
    city_prefix = "Казань" 

    if query:
        canteens = Canteen.objects.filter(
            Q(name__icontains=query) | Q(address__icontains=query)
        )
    else:
        canteens = Canteen.objects.all()

    return render(request, "search.html", {
        "canteens": canteens,
        "query": query,
        "city_prefix": city_prefix  # ПРОВЕРЬ ЭТУ СТРОКУ
    })



def canteen_detail(request, id):
    canteen = get_object_or_404(Canteen, id=id)
    return render(request, "canteen_detail.html", {"canteen": canteen})