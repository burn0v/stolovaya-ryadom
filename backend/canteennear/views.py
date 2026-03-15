from django.shortcuts import render
from .models import Canteen

def home(request):

    canteens = Canteen.objects.all()   # получаем все столовые из базы

    return render(request, "home.html", {"canteens": canteens})