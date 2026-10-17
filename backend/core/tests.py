from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.test import TestCase

from catalog.models import Category, Product, ProductImage, ProductSize, Size, Tag

from .models import Address, Subscriber

User = get_user_model()


def make_category(name: str, parent: Category | None = None, **kwargs) -> Category:
    return Category.objects.create(name=name, parent=parent, **kwargs)


def make_product(category: Category | None = None, name: str = "Fern Pot", **kwargs) -> Product:
    if category is None:
        category = make_category(f"Cat for {name}")
    kwargs.setdefault("price", Decimal("19.99"))
    kwargs.setdefault("stock", 10)
    return Product.objects.create(category=category, name=name, **kwargs)


def make_size(name: str, ordering: int = 0) -> Size:
    return Size.objects.create(name=name, ordering=ordering)


def make_product_size(product: Product, size: Size, **kwargs) -> ProductSize:
    kwargs.setdefault("stock", 5)
    return ProductSize.objects.create(product=product, size=size, **kwargs)


def make_image(product: Product, name: str = "products/test.jpg", **kwargs) -> ProductImage:
    return ProductImage.objects.create(product=product, image=name, **kwargs)


def make_tag(name: str, **kwargs) -> Tag:
    return Tag.objects.create(name=name, **kwargs)


class ViewSmokeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = make_category("House Plants")
        self.child = make_category("Indoor Plants", parent=self.root)
        self.product = make_product(self.child, name="Monstera Deliciosa", price=Decimal("24.50"), stock=5)
        make_image(self.product)
        small = make_size("Small")
        make_product_size(self.product, small, stock=5)
        make_tag("Care Tips")

    def test_public_pages_render(self):
        paths = [
            "/",
            "/shop/",
            f"/shop/category/{self.root.slug}/",
            f"/shop/category/{self.child.slug}/",
            f"/product/{self.product.slug}/",
            "/cart/",
            "/login/",
            "/register/",
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, path)

    def test_wishlist_anonymous_redirects_to_login(self):
        response = self.client.get("/wishlist/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_checkout_redirects_when_the_cart_is_empty(self):
        response = self.client.get("/checkout/")
        self.assertRedirects(response, "/cart/")

    def test_checkout_renders_when_the_cart_has_items(self):
        added = self.client.post(f"/cart/add/{self.product.pk}/", {"quantity": 2})
        self.assertEqual(added.status_code, 302)
        response = self.client.get("/checkout/")
        self.assertEqual(response.status_code, 200)

    def test_account_and_orders_redirect_anonymous_to_login(self):
        for path in ("/account/", "/orders/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertRedirects(response, f"/login/?next={path}")

    def test_account_and_orders_render_for_a_signed_in_user(self):
        user = User.objects.create_user(username="alice", password="hunter2pass")
        self.client.force_login(user)
        for path in ("/account/", "/orders/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, path)


class HomeViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = make_category("House Plants")
        self.child = make_category("Indoor Plants", parent=self.root)
        self.tools = make_category("Garden Tools")

        self.featured = make_product(self.root, name="Featured Fern", is_featured=True)
        self.plain = make_product(self.child, name="Plain Pothos")
        self.sale = make_product(self.root, name="Sale Cactus",
                                 price=Decimal("10.00"), old_price=Decimal("20.00"))
        make_product(self.root, name="Retired Fern", is_active=False)
        self.trowel = make_product(self.tools, name="Steel Trowel")

        self.small = make_size("Small")
        self.medium = make_size("Medium", ordering=1)
        make_product_size(self.featured, self.small)
        make_product_size(self.plain, self.small)
        make_product_size(Product.objects.get(name="Retired Fern"), self.medium)

        make_tag("Care Tips")
        make_tag("Hidden", is_active=False)

    def test_home_context(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        ctx = response.context

        pks = [p.pk for p in ctx["products"]]
        self.assertEqual(pks[0], self.featured.pk)
        self.assertCountEqual(pks, [self.featured.pk, self.plain.pk, self.sale.pk, self.trowel.pk])
        self.assertEqual([p.pk for p in ctx["hero_products"]], pks[:3])

        rows = {row["category"].pk: row for row in ctx["category_rows"]}
        self.assertEqual(rows[self.root.pk]["count"], 3)
        self.assertEqual(rows[self.tools.pk]["count"], 1)
        children = {row["category"].pk: row for row in rows[self.root.pk]["children"]}
        self.assertEqual(children[self.child.pk]["count"], 1)

        size_counts = {row["size"].name: row["count"] for row in ctx["size_rows"]}
        self.assertEqual(size_counts, {"Small": 2, "Medium": 0})

        self.assertEqual([t.name for t in ctx["tags"]], ["Care Tips"])
        self.assertEqual([p.pk for p in ctx["sale_products"]], [self.sale.pk])

    def test_home_renders_the_blog_section(self):
        response = self.client.get("/")
        self.assertContains(response, "Our Blog Posts")


REGISTER_PAYLOAD = {
    "username": "olivia.t",
    "first_name": "Olivia",
    "last_name": "Thorne",
    "email": "olivia@example.com",
    "phone": "+380501112233",
    "password1": "V3ryUn1que!Zz",
    "password2": "V3ryUn1que!Zz",
}


class RegisterTests(TestCase):
    def test_register_creates_the_user_and_signs_them_in(self):
        response = self.client.post("/register/", REGISTER_PAYLOAD)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        user = User.objects.get(username="olivia.t")
        self.assertEqual(user.email, "olivia@example.com")
        self.assertEqual(user.first_name, "Olivia")
        self.assertEqual(user.role, User.Role.CLIENT)
        self.assertTrue(user.check_password(REGISTER_PAYLOAD["password1"]))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(any(m.level == messages.SUCCESS for m in get_messages(response.wsgi_request)))

    def test_duplicate_username_renders_the_form_with_an_error(self):
        User.objects.create_user(username="olivia.t", password="hunter2pass")
        payload = dict(REGISTER_PAYLOAD, email="other@example.com")
        before = User.objects.count()

        response = self.client.post("/register/", payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(User.objects.count(), before)

    def test_authenticated_visitor_is_redirected_away_from_register(self):
        user = User.objects.create_user(username="olivia.t", password="hunter2pass")
        self.client.force_login(user)
        response = self.client.get("/register/")
        self.assertRedirects(response, "/account/")


class LoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="hunter2pass")

    def test_login_with_good_credentials(self):
        response = self.client.post("/login/", {"username": "bob", "password": "hunter2pass"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_with_a_bad_password_renders_an_error(self):
        response = self.client.post("/login/", {"username": "bob", "password": "wrong-pass"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_with_an_unknown_user_renders_an_error(self):
        response = self.client.post("/login/", {"username": "ghost", "password": "whatever1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)


class LogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dana", password="hunter2pass")
        self.client.force_login(self.user)

    def test_post_logout_ends_the_session_and_redirects_home(self):
        response = self.client.post("/logout/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.get("/account/"), "/login/?next=/account/")

    def test_get_logout_never_ends_the_session(self):
        response = self.client.get("/logout/")

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get("/account/").status_code, 200)

    def test_post_logout_for_an_anonymous_visitor_is_still_safe(self):
        self.client.logout()
        response = self.client.post("/logout/")

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class SubscribeTests(TestCase):
    def test_subscribe_creates_a_subscriber(self):
        response = self.client.post("/subscribe/", {"email": "Fan@Example.COM"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertTrue(Subscriber.objects.filter(email="fan@example.com").exists())
        levels = [m.level for m in get_messages(response.wsgi_request)]
        self.assertIn(messages.SUCCESS, levels)

    def test_duplicate_email_is_a_message_not_a_500(self):
        Subscriber.objects.create(email="fan@example.com")

        response = self.client.post("/subscribe/", {"email": "fan@example.com"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Subscriber.objects.count(), 1)
        levels = [m.level for m in get_messages(response.wsgi_request)]
        self.assertIn(messages.INFO, levels)

    def test_reactivating_an_unsubscribed_address(self):
        Subscriber.objects.create(email="fan@example.com", is_active=False)
        response = self.client.post("/subscribe/", {"email": "fan@example.com"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subscriber.objects.get(email="fan@example.com").is_active)

    def test_blank_email_redirects_with_an_error_message(self):
        response = self.client.post("/subscribe/", {"email": ""})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Subscriber.objects.count(), 0)
        levels = [m.level for m in get_messages(response.wsgi_request)]
        self.assertIn(messages.ERROR, levels)


class AddressFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="addrfan", password="hunter2pass")
        self.client.force_login(self.user)

    @staticmethod
    def address_data(**overrides):
        data = {
            "label": "home",
            "full_name": "Jane Doe",
            "phone": "+380501234567",
            "line1": "Green Street 1",
            "line2": "",
            "city": "Kyiv",
            "region": "",
            "postal_code": "01001",
            "country": "USA",
            "is_default": "on",
        }
        data.update(overrides)
        return data

    def make_address(self, **kwargs):
        defaults = self.address_data()
        defaults.pop("is_default")
        defaults.update(kwargs)
        return Address.objects.create(user=self.user, **defaults)

    def test_list_renders_for_a_signed_in_user(self):
        self.make_address()
        response = self.client.get("/account/addresses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["addresses"]), 1)

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        for path in ("/account/addresses/", "/account/addresses/add/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertRedirects(response, f"/login/?next={path}")

    def test_create_flow(self):
        response = self.client.get("/account/addresses/add/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/account/addresses/add/", self.address_data())
        self.assertRedirects(response, "/account/addresses/")
        address = Address.objects.get()
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.city, "Kyiv")
        self.assertTrue(address.is_default)

    def test_invalid_create_renders_the_form_with_errors(self):
        response = self.client.post("/account/addresses/add/", self.address_data(line1="", city=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("line1", response.context["form"].errors)
        self.assertIn("city", response.context["form"].errors)
        self.assertEqual(Address.objects.count(), 0)

    def test_update_flow(self):
        address = self.make_address()
        url = f"/account/addresses/{address.pk}/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, self.address_data(city="Lviv"))
        self.assertRedirects(response, "/account/addresses/")
        address.refresh_from_db()
        self.assertEqual(address.city, "Lviv")

    def test_update_needs_the_address_of_the_signed_in_user(self):
        other = User.objects.create_user(username="otherfan", password="hunter2pass")
        theirs = Address.objects.create(
            user=other, full_name="Them", line1="Their Street", city="Odesa"
        )
        response = self.client.post(
            f"/account/addresses/{theirs.pk}/", self.address_data(city="Hacked")
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_flow(self):
        address = self.make_address()
        response = self.client.post(f"/account/addresses/{address.pk}/delete/")
        self.assertRedirects(response, "/account/addresses/")
        self.assertFalse(Address.objects.filter(pk=address.pk).exists())

    def test_delete_requires_post(self):
        address = self.make_address()
        response = self.client.get(f"/account/addresses/{address.pk}/delete/")
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Address.objects.filter(pk=address.pk).exists())
