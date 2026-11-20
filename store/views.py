from django.shortcuts import render, get_object_or_404
from .models import Product, CartItem, Order, OrderItem
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import Product, CartItem, Order, OrderItem, Category
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib import messages


SORT_OPTIONS = {
    "price_asc": ["price"],
    "price_desc": ["-price"],
    "new": ["-id"],
    "name": ["name"],
    "popular": ["-sold", "name"],
}


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    category_id = request.GET.get("category")
    if category_id and category_id.isdigit():
        products = products.filter(category_id=category_id)

    query = request.GET.get("q", "")
    if query:
        products = products.filter(name__icontains=query)

    sort = request.GET.get("sort", "")
    if sort == "popular":
        products = products.annotate(sold=Coalesce(Sum("orderitem__quantity"), 0))
    if sort in SORT_OPTIONS:
        products = products.order_by(*SORT_OPTIONS[sort])

    return render(request, "store/product_list.html", {
        "products": products,
        "categories": categories,
        "selected_category": category_id,
        "query": query,
        "sort": sort,
    })

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

@login_required     #декоратор
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"«{product.name}» добавлен в корзину")
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
    messages.success(request, f"«{item.product.name}» удалён из корзины")
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
    messages.success(request, f"Заказ №{order.id} оформлен! Спасибо за покупку.")

    return redirect("orders")

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/orders.html", {"orders": orders})


@login_required
@require_POST
def cart_increase(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.quantity += 1
    item.save()
    return redirect("cart")


@login_required
@require_POST
def cart_decrease(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect("cart")

def help_view(request):
    return render(request, "store/help.html")


def delivery_view(request):
    return render(request, "store/delivery.html")


def contacts_view(request):
    return render(request, "store/contacts.html")