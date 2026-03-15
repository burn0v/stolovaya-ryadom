from django.shortcuts import render, get_object_or_404
from .models import Canteen

def home(request):

    canteens = Canteen.objects.all()   # получаем все столовые из базы

    return render(request, "home.html", {"canteens": canteens})

def canteen_detail(request, id):
    canteen = get_object_or_404(Canteen, id=id)
    return render(request, "canteen_detail.html", {"canteen": canteen})