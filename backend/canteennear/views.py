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
        "city_prefix": city_prefix
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