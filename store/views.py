from django.shortcuts import render, get_object_or_404
from .models import Product
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect

def product_list(request):
    products = Product.objects.all()
    return render(request, "store/product_list.html", {"products": products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "store/product_detail.html", {"product": product})

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("product_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})