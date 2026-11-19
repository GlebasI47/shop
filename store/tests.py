from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from .models import Category, Product, CartItem, Order, OrderItem


#Unit и Интеграционные
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


class CartAndOrderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="StrongPass123")
        self.other = User.objects.create_user(username="other", password="StrongPass123")
        category = Category.objects.create(name="Телефоны")
        self.product = Product.objects.create(
            category=category, name="Айфон", price=Decimal("1000.00")
        )
        self.client.login(username="buyer", password="StrongPass123")

    def test_add_same_product_twice_increases_quantity(self):
        url = reverse("add_to_cart", args=[self.product.id])
        self.client.post(url)
        self.client.post(url)
        item = CartItem.objects.get(user=self.user, product=self.product)
        self.assertEqual(item.quantity, 2)

    def test_cannot_remove_other_users_item(self):
        item = CartItem.objects.create(user=self.other, product=self.product)
        response = self.client.post(reverse("remove_from_cart", args=[item.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(id=item.id).exists())

    def test_checkout_empty_cart_returns_400(self):
        response = self.client.post(reverse("checkout"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_creates_order_and_clears_cart(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.post(reverse("checkout"))
        self.assertRedirects(response, reverse("orders"))

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total, Decimal("2000.00"))
        order_item = OrderItem.objects.get(order=order)
        self.assertEqual(order_item.price, Decimal("1000.00"))
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)


    def test_cart_increase_and_decrease(self):
        item = CartItem.objects.create(user=self.user, product=self.product, quantity=1)

        self.client.post(reverse("cart_increase", args=[item.id]))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

        self.client.post(reverse("cart_decrease", args=[item.id]))
        self.client.post(reverse("cart_decrease", args=[item.id]))
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())


class RegistrationTests(TestCase):
    def test_weak_password_shows_errors(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "12345678",
            "password2": "12345678",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertTrue(response.context["form"].errors)


class CatalogTests(TestCase):
    def setUp(self):
        phones = Category.objects.create(name="Телефоны")
        headphones = Category.objects.create(name="Наушники")
        self.phones = phones
        Product.objects.create(category=phones, name="iPhone", price=Decimal("1000.00"))
        Product.objects.create(category=headphones, name="AirPods", price=Decimal("400.00"))

    def test_filter_by_category(self):
        response = self.client.get(reverse("product_list"), {"category": self.phones.id})
        self.assertContains(response, "iPhone")
        self.assertNotContains(response, "AirPods")

    def test_search_ignores_case(self):
        response = self.client.get(reverse("product_list"), {"q": "airpods"})
        self.assertContains(response, "AirPods")
        self.assertNotContains(response, "iPhone")

    def test_bad_category_does_not_break_page(self):
        response = self.client.get(reverse("product_list"), {"category": "abc"})
        self.assertEqual(response.status_code, 200)