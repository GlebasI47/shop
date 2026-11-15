from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from .models import Category, Product, CartItem


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="StrongPass123")
        self.category = Category.objects.create(name="Телефоны")
        self.product = Product.objects.create(
            category=self.category, name="Айфон", price=Decimal("1000.00")
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), "Айфон")

    def test_cart_item_total_price(self):
        item = CartItem.objects.create(user=self.user, product=self.product, quantity=3)
        self.assertEqual(item.total_price(), Decimal("3000.00"))


class AccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="StrongPass123")
        category = Category.objects.create(name="Телефоны")
        self.product = Product.objects.create(
            category=category, name="Айфон", price=Decimal("1000.00")
        )

    def test_catalog_shows_products(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Айфон")

    def test_missing_product_returns_404(self):
        response = self.client.get(reverse("product_detail", args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_add_to_cart_requires_login(self):
        response = self.client.post(reverse("add_to_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_add_to_cart_get_not_allowed(self):
        self.client.login(username="buyer", password="StrongPass123")
        response = self.client.get(reverse("add_to_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 405)