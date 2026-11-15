from django.shortcuts import render, get_object_or_404
from .models import Product, CartItem, Order, OrderItem
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction


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

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    return redirect("product_detail", product_id=product.id)

@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user)
    total = 0
    for item in items:
        total = total + item.total_price()
    return render(request, "store/cart.html", {"items": items, "total": total})

@login_required
@require_POST
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect("cart")

@login_required
@require_POST
def checkout(request):
    items = CartItem.objects.filter(user=request.user)
    if not items:
        return render(request, "store/cart.html",
                      {"items": items, "total": 0, "error": "Корзина пуста, нечего оформлять."},
                      status=400)

    with transaction.atomic():
        order = Order.objects.create(user=request.user)
        total = 0
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
            total = total + item.total_price()
        order.total = total
        order.save()
        items.delete()

    return redirect("cart")