from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.signals import got_request_exception
from django.db import connection
from django.db.models import Value
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext

from catalog.models import Category, Product, ProductSize, Size, Wishlist

from . import services
from .models import Cart, CartItem, Order

User = get_user_model()

ANON_SESSION_KEY = "anon-session-0123456789abcdef"
AUTH_SESSION_KEY = "auth-session-0123456789abcdef"
OTHER_SESSION_KEY = "nobody-0123456789abcdef"


def make_category(name: str = "House Plants") -> Category:
    return Category.objects.create(name=name)


def make_product(name: str = "Fern Pot", **kwargs) -> Product:
    if "category" not in kwargs:
        kwargs["category"] = make_category(f"Cat for {name}")
    kwargs.setdefault("price", Decimal("10.00"))
    kwargs.setdefault("stock", 10)
    return Product.objects.create(name=name, **kwargs)


def make_size(name: str = "Large") -> Size:
    return Size.objects.create(name=name)


def make_product_size(product: Product, size: Size, **kwargs) -> ProductSize:
    kwargs.setdefault("stock", 5)
    return ProductSize.objects.create(product=product, size=size, **kwargs)


def add_line(cart: Cart, product: Product, quantity: int = 1, size=None) -> CartItem:
    return CartItem.objects.create(cart=cart, product=product, size=size, quantity=quantity)


def make_request(user=None, session_key: str | None = None):
    request = RequestFactory().get("/")
    request.user = user if user is not None else AnonymousUser()
    request.session = SessionStore(session_key=session_key)
    return request


class CartFixtureMixin:
    def build_basket(self):
        self.user = User.objects.create_user(username="cartfan", password="hunter2pass")
        self.product = make_product(name="Fern Pot", price=Decimal("10.00"), stock=10)
        self.sized_product = make_product(name="Violet Pot", price=Decimal("5.00"), stock=10)
        self.size = make_size("Large")
        self.product_size = make_product_size(
            self.sized_product, self.size, price_delta=Decimal("1.00"), stock=5
        )
        self.cart = Cart.objects.create(user=self.user)
        add_line(self.cart, self.product, quantity=2)
        add_line(self.cart, self.sized_product, quantity=1, size=self.product_size)
        self.cart_pk = self.cart.pk


class CartItemsMemoTests(CartFixtureMixin, TestCase):
    def setUp(self):
        self.build_basket()

    def test_all_figures_share_one_lines_query(self):
        cart = Cart.objects.get(pk=self.cart_pk)
        with CaptureQueriesContext(connection) as ctx:
            subtotal = cart.subtotal
            discount = cart.discount
            total = cart.total
            is_empty = cart.is_empty
            item_count = cart.item_count

        line_queries = [q for q in ctx.captured_queries if "orders_cartitem" in q["sql"]]
        self.assertEqual(
            len(line_queries), 1,
            "subtotal/discount/total/is_empty/item_count must share one lines fetch",
        )
        self.assertEqual(subtotal, Decimal("26.00"))
        self.assertEqual(discount, Decimal("0.00"))
        self.assertEqual(total, Decimal("26.00"))
        self.assertFalse(is_empty)
        self.assertEqual(item_count, 3)

        with self.assertNumQueries(0):
            self.assertEqual(cart.subtotal, Decimal("26.00"))
            self.assertEqual(cart.total, Decimal("26.00"))
            self.assertEqual(cart.item_count, 3)
            self.assertFalse(cart.is_empty)

    def test_lines_arrive_with_product_and_size_attached(self):
        cart = Cart.objects.get(pk=self.cart_pk)
        with self.assertNumQueries(2):
            lines = list(cart.items)
        with self.assertNumQueries(0):
            names = [line.product.name for line in lines]
            labels = [line.size_label for line in lines]
        self.assertEqual(names, ["Fern Pot", "Violet Pot"])
        self.assertEqual(labels, ["", "Large"])
        self.assertEqual([line.line_total for line in lines], [Decimal("20.00"), Decimal("6.00")])

    def test_item_count_uses_the_annotated_badge(self):
        request = make_request(user=self.user)
        cart = services.get_cart(request)
        self.assertTrue(hasattr(cart, "badge_count"))
        with self.assertNumQueries(0):
            self.assertEqual(cart.item_count, 3)

    def test_badge_wins_even_when_it_disagrees_with_the_lines(self):
        annotated = Cart.objects.annotate(badge_count=Value(42)).get(pk=self.cart_pk)
        with self.assertNumQueries(0):
            self.assertEqual(annotated.item_count, 42)

    def test_item_count_falls_back_to_summing_lines(self):
        cart = Cart.objects.get(pk=self.cart_pk)
        with self.assertNumQueries(2):
            self.assertEqual(cart.item_count, 3)

    def test_clear_empties_lines_resets_coupon_and_drops_the_memo(self):
        cart = Cart.objects.get(pk=self.cart_pk)
        cart.coupon_code = "GREEN10"
        cart.coupon_discount = Decimal("5.00")
        cart.save()
        self.assertEqual(len(cart.items), 2)

        cart.clear()

        self.assertEqual(cart.coupon_code, "")
        self.assertEqual(cart.coupon_discount, Decimal("0.00"))
        self.assertEqual(CartItem.objects.filter(cart_id=self.cart_pk).count(), 0)
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(cart.items, [])
        self.assertTrue(
            any("orders_cartitem" in q["sql"] for q in ctx.captured_queries),
            "clear() must invalidate the memo so the next read re-queries",
        )
        with self.assertNumQueries(0):
            self.assertEqual(cart.item_count, 0)
            self.assertTrue(cart.is_empty)


class GetCartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="hunter2pass")
        self.product = make_product(name="Money Tree", price=Decimal("10.00"))

    def test_two_calls_share_one_row_query_for_a_user_cart(self):
        cart = Cart.objects.create(user=self.user)
        add_line(cart, self.product, quantity=2)
        request = make_request(user=self.user, session_key=AUTH_SESSION_KEY)
        with self.assertNumQueries(1):
            first = services.get_cart(request)
            second = services.get_cart(request)
        self.assertIs(first, second)
        with self.assertNumQueries(0):
            self.assertEqual(first.item_count, 2)

    def test_two_calls_share_one_row_query_for_an_anonymous_cart(self):
        Cart.objects.create(session_key=ANON_SESSION_KEY)
        request = make_request(session_key=ANON_SESSION_KEY)
        with self.assertNumQueries(1):
            first = services.get_cart(request)
            second = services.get_cart(request)
        self.assertIs(first, second)

    def test_missing_cart_without_create_returns_none(self):
        request = make_request(session_key=ANON_SESSION_KEY)
        self.assertIsNone(services.get_cart(request))
        with self.assertNumQueries(0):
            self.assertIsNone(services.get_cart(request))

    def test_create_true_creates_an_anonymous_cart(self):
        request = make_request(session_key=ANON_SESSION_KEY)
        with self.assertNumQueries(2):
            cart = services.get_cart(request, create=True)
        self.assertEqual(cart.session_key, ANON_SESSION_KEY)
        self.assertIsNone(cart.user)
        with self.assertNumQueries(0):
            self.assertIs(services.get_cart(request, create=True), cart)

    def test_create_true_creates_a_user_cart(self):
        request = make_request(user=self.user, session_key=AUTH_SESSION_KEY)
        cart = services.get_cart(request, create=True)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

    def test_anonymous_visitor_without_a_session_gets_one(self):
        request = make_request()
        cart = services.get_cart(request, create=True)
        self.assertIsNotNone(request.session.session_key)
        self.assertEqual(cart.session_key, request.session.session_key)

    def test_sign_in_adopts_the_anonymous_cart(self):
        anon = Cart.objects.create(session_key=ANON_SESSION_KEY)
        line = add_line(anon, self.product, quantity=2)
        request = make_request(user=self.user, session_key=ANON_SESSION_KEY)
        cart = services.get_cart(request, create=True)
        self.assertEqual(cart.pk, anon.pk)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
        self.assertFalse(Cart.objects.filter(session_key=ANON_SESSION_KEY).exists())
        line.refresh_from_db()
        self.assertEqual(line.cart_id, cart.pk)
        self.assertEqual(cart.item_count, 2)

    def test_user_without_a_session_never_adopts_a_strangers_cart(self):
        stranger = User.objects.create_user(username="stranger", password="hunter2pass")
        stranger_cart = Cart.objects.create(user=stranger)
        add_line(stranger_cart, self.product, quantity=1)

        request = make_request(user=self.user)
        cart = services.get_cart(request, create=True)

        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.item_count, 0)
        self.assertTrue(Cart.objects.filter(user=stranger, pk=stranger_cart.pk).exists())

    def test_attach_cart_to_user_merges_matching_lines(self):
        other_product = make_product(name="Cactus Mate")
        sized_mate = make_product(name="Sized Mate")
        user_cart = Cart.objects.create(user=self.user)
        keep_dup = add_line(user_cart, self.product, quantity=3)
        keep_other = add_line(user_cart, other_product, quantity=1)
        anon = Cart.objects.create(session_key=ANON_SESSION_KEY)
        anon_dup = add_line(anon, self.product, quantity=2)
        anon_moved = add_line(anon, sized_mate, quantity=4)

        result = services.attach_cart_to_user(anon, self.user)

        self.assertEqual(result.pk, user_cart.pk)
        keep_dup.refresh_from_db()
        self.assertEqual(keep_dup.quantity, 5)
        keep_other.refresh_from_db()
        self.assertEqual(keep_other.cart_id, user_cart.pk)
        anon_moved.refresh_from_db()
        self.assertEqual(anon_moved.cart_id, user_cart.pk)
        with self.assertRaises(CartItem.DoesNotExist):
            anon_dup.refresh_from_db()
        self.assertFalse(Cart.objects.filter(pk=anon.pk).exists())

    def test_attach_cart_to_user_handles_anon_pk_equal_to_existing(self):
        cart = Cart.objects.create(user=self.user)
        result = services.attach_cart_to_user(cart, self.user)
        self.assertEqual(result.pk, cart.pk)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)


class AddToCartTests(TestCase):
    def setUp(self):
        self.request = make_request(session_key=ANON_SESSION_KEY)
        self.product = make_product(name="Fern Pot", price=Decimal("10.00"), stock=10)
        self.sized_product = make_product(name="Violet Pot", price=Decimal("5.00"), stock=10)
        self.size = make_size("Large")
        self.product_size = make_product_size(
            self.sized_product, self.size, price_delta=Decimal("1.00"), stock=5
        )

    def test_creates_a_line_and_a_cart(self):
        line = services.add_to_cart(self.request, self.product, quantity=2)
        self.assertEqual(line.quantity, 2)
        cart = services.get_cart(self.request)
        self.assertEqual(cart.item_count, 2)

    def test_tops_up_an_existing_line(self):
        services.add_to_cart(self.request, self.product, quantity=2)
        line = services.add_to_cart(self.request, self.product, quantity=3)
        self.assertEqual(line.quantity, 5)
        self.assertEqual(CartItem.objects.filter(cart__session_key=ANON_SESSION_KEY).count(), 1)

    def test_stores_the_selected_size(self):
        line = services.add_to_cart(self.request, self.sized_product, size=self.product_size)
        self.assertEqual(line.size_id, self.product_size.pk)
        self.assertEqual(line.unit_price, Decimal("6.00"))

    def test_rejects_an_inactive_product(self):
        retired = make_product(name="Retired Fern", is_active=False)
        with self.assertRaises(ValidationError) as ctx:
            services.add_to_cart(self.request, retired)
        self.assertIn("no longer for sale", ctx.exception.messages[0])
        self.assertFalse(Cart.objects.filter(session_key=ANON_SESSION_KEY).exists())

    def test_rejects_insufficient_product_stock(self):
        with self.assertRaises(ValidationError) as ctx:
            services.add_to_cart(self.request, self.product, quantity=11)
        self.assertIn("Only 10 left", ctx.exception.messages[0])

    def test_rejects_insufficient_size_stock(self):
        with self.assertRaises(ValidationError) as ctx:
            services.add_to_cart(self.request, self.sized_product, size=self.product_size, quantity=6)
        self.assertIn("Only 5 left", ctx.exception.messages[0])

    def test_model_guards_the_stock_when_topping_up(self):
        services.add_to_cart(self.request, self.product, quantity=8)
        with self.assertRaises(ValidationError):
            services.add_to_cart(self.request, self.product, quantity=4)


class CartQuantityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="qtyfan", password="hunter2pass")
        self.request = make_request(user=self.user, session_key=AUTH_SESSION_KEY)
        self.product = make_product(name="Fern Pot", price=Decimal("10.00"), stock=10)
        self.line = services.add_to_cart(self.request, self.product, quantity=2)

    def test_set_quantity_updates_the_line(self):
        returned = services.set_quantity(self.request, self.line.pk, 7)
        self.assertEqual(returned.quantity, 7)
        self.line.refresh_from_db()
        self.assertEqual(self.line.quantity, 7)

    def test_set_quantity_at_zero_deletes_the_line(self):
        result = services.set_quantity(self.request, self.line.pk, 0)
        self.assertIsNone(result)
        self.assertFalse(CartItem.objects.filter(pk=self.line.pk).exists())

    def test_set_quantity_for_a_missing_line_returns_none(self):
        self.assertIsNone(services.set_quantity(self.request, self.line.pk + 999, 3))

    def test_set_quantity_without_a_cart_returns_none(self):
        other = make_request(session_key=OTHER_SESSION_KEY)
        self.assertIsNone(services.set_quantity(other, self.line.pk, 3))

    def test_remove_line_deletes_and_invalidates_the_memo(self):
        cart = services.get_cart(self.request)
        self.assertEqual(len(cart.items), 1)
        services.remove_line(self.request, self.line.pk)
        self.assertFalse(CartItem.objects.filter(pk=self.line.pk).exists())
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(cart.items, [])
        self.assertTrue(
            any("orders_cartitem" in q["sql"] for q in ctx.captured_queries),
            "remove_line() must invalidate the memo so the next read re-queries",
        )
        with self.assertNumQueries(0):
            self.assertEqual(cart.items, [])


class CouponTests(CartFixtureMixin, TestCase):
    def setUp(self):
        self.build_basket()
        self.request = make_request(user=self.user)

    def test_green10_gives_ten_percent_of_the_subtotal(self):
        cart = services.apply_coupon(self.request, "green10")
        self.assertEqual(cart.coupon_code, "GREEN10")
        self.assertEqual(cart.coupon_discount, Decimal("2.60"))
        self.assertEqual(cart.discount, Decimal("2.60"))
        self.assertEqual(cart.total, Decimal("23.40"))

    def test_green10_discount_is_quantized(self):
        add_line(self.cart, make_product(name="Odd Priced", price=Decimal("33.33"), stock=5))
        cart = services.apply_coupon(self.request, "GREEN10")
        self.assertEqual(cart.coupon_discount, Decimal("5.93"))

    def test_an_unknown_code_clears_the_discount(self):
        services.apply_coupon(self.request, "GREEN10")
        cart = services.apply_coupon(self.request, "SAVE20")
        self.assertEqual(cart.coupon_code, "")
        self.assertEqual(cart.coupon_discount, Decimal("0.00"))
        stored = Cart.objects.get(pk=cart.pk)
        self.assertEqual(stored.coupon_discount, Decimal("0.00"))

    def test_discount_never_exceeds_the_subtotal(self):
        cart = Cart.objects.get(pk=self.cart_pk)
        cart.coupon_discount = Decimal("500.00")
        cart.save()
        self.assertEqual(cart.discount, cart.subtotal)
        self.assertEqual(cart.total, Decimal("0.00"))


class PlaceOrderTests(CartFixtureMixin, TestCase):
    def setUp(self):
        self.build_basket()
        self.request = make_request(user=self.user, session_key=AUTH_SESSION_KEY)

    def place(self, **overrides):
        defaults = dict(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="+380501234567",
            address_line="Green Street 1",
            city="Kyiv",
        )
        defaults.update(overrides)
        return services.place_order(self.request, **defaults)

    def test_no_cart_at_all_is_rejected(self):
        request = make_request(session_key=OTHER_SESSION_KEY)
        with self.assertRaises(ValidationError) as ctx:
            services.place_order(request, full_name="X", email="x@example.com", phone="",
                                 address_line="1 Main St", city="Lviv")
        self.assertIn("empty", ctx.exception.messages[0])
        self.assertEqual(Order.objects.count(), 0)

    def test_cart_without_lines_is_rejected(self):
        Cart.objects.filter(pk=self.cart_pk).delete()
        Cart.objects.create(user=self.user)
        with self.assertRaises(ValidationError):
            self.place()
        self.assertEqual(Order.objects.count(), 0)

    def test_places_order_clears_cart_and_decrements_stock(self):
        order = self.place()

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.user, self.user)
        self.assertTrue(order.number.startswith("GS-"))
        self.assertEqual(order.status, Order.Status.NEW)
        self.assertEqual(order.full_name, "Jane Doe")
        self.assertEqual(order.subtotal, Decimal("26.00"))
        self.assertEqual(order.discount, Decimal("0.00"))
        self.assertEqual(order.shipping, Decimal("9.00"))
        self.assertEqual(order.total, Decimal("35.00"))

        self.assertEqual(order.items.count(), 2)
        first_item, second_item = order.items.order_by("pk")
        self.assertEqual(first_item.product_id, self.product.pk)
        self.assertEqual(first_item.product_name, "Fern Pot")
        self.assertEqual(first_item.product_slug, self.product.slug)
        self.assertEqual(first_item.sku, self.product.sku)
        self.assertEqual(first_item.size_name, "")
        self.assertEqual(first_item.quantity, 2)
        self.assertEqual(first_item.unit_price, Decimal("10.00"))
        self.assertEqual(first_item.line_total, Decimal("20.00"))
        self.assertEqual(second_item.product_id, self.sized_product.pk)
        self.assertEqual(second_item.size_name, "Large")
        self.assertEqual(second_item.unit_price, Decimal("6.00"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

        fresh = Cart.objects.get(pk=self.cart_pk)
        self.assertEqual(CartItem.objects.filter(cart=fresh).count(), 0)
        self.assertEqual(fresh.coupon_code, "")
        self.assertEqual(fresh.coupon_discount, Decimal("0.00"))
        self.assertTrue(fresh.is_empty)

    def test_sized_line_decrements_both_stocks(self):
        Cart.objects.filter(pk=self.cart_pk).delete()
        plant = make_product(name="Big Violet", price=Decimal("20.00"), stock=10)
        row = make_product_size(plant, make_size("Medium"), price_delta=Decimal("5.00"), stock=5)
        services.add_to_cart(self.request, plant, size=row, quantity=2)
        order = self.place()

        item = order.items.get()
        self.assertEqual(item.size_name, "Medium")
        self.assertEqual(item.unit_price, Decimal("25.00"))
        self.assertEqual(item.line_total, Decimal("50.00"))

        plant.refresh_from_db()
        self.assertEqual(plant.stock, 8)
        row.refresh_from_db()
        self.assertEqual(row.stock, 3)

    def test_free_shipping_at_the_threshold(self):
        Cart.objects.filter(pk=self.cart_pk).delete()
        big = make_product(name="Big Olive", price=Decimal("150.00"), stock=3)
        services.add_to_cart(self.request, big, quantity=1)
        order = self.place()
        self.assertEqual(order.subtotal, Decimal("150.00"))
        self.assertEqual(order.shipping, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("150.00"))

    def test_shipping_cost_thresholds(self):
        self.assertEqual(services.shipping_cost(Decimal("119.99")), Decimal("9.00"))
        self.assertEqual(services.shipping_cost(Decimal("120.00")), Decimal("0.00"))

    def test_coupon_discount_moves_shipping_onto_the_net_subtotal(self):
        Cart.objects.filter(pk=self.cart_pk).delete()
        services.add_to_cart(self.request, self.product, quantity=10)
        services.apply_coupon(self.request, "GREEN10")
        order = self.place()
        self.assertEqual(order.subtotal, Decimal("100.00"))
        self.assertEqual(order.discount, Decimal("10.00"))
        self.assertEqual(order.coupon_code, "GREEN10")
        self.assertEqual(order.shipping, Decimal("9.00"))
        self.assertEqual(order.total, Decimal("99.00"))

    def test_anonymous_order_has_no_user(self):
        Cart.objects.filter(pk=self.cart_pk).delete()
        request = make_request(session_key=ANON_SESSION_KEY)
        services.add_to_cart(request, self.product, quantity=1)
        order = services.place_order(
            request, full_name="Anon", email="anon@example.com", phone="",
            address_line="1 Main St", city="Lviv",
        )
        self.assertIsNone(order.user)
        self.assertEqual(order.total, Decimal("19.00"))


class AtomicWritesMiddlewareTests(TransactionTestCase):
    def run_middleware(self, method: str):
        from core.middleware import AtomicWritesMiddleware

        request = getattr(RequestFactory(), method.lower())("/")
        seen = {}

        def get_response(req):
            seen["in_atomic"] = connection.in_atomic_block
            return HttpResponse("ok")

        response = AtomicWritesMiddleware(get_response)(request)
        return seen, response

    def test_read_methods_do_not_open_a_transaction(self):
        for method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            seen, response = self.run_middleware(method)
            with self.subTest(method=method):
                self.assertFalse(seen["in_atomic"], f"{method} must not open a transaction")
                self.assertEqual(response.status_code, 200)

    def test_write_methods_open_a_transaction(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            seen, response = self.run_middleware(method)
            with self.subTest(method=method):
                self.assertTrue(seen["in_atomic"], f"{method} must run inside a transaction")
                self.assertEqual(response.status_code, 200)

    def test_exception_signal_rolls_back_a_failed_write(self):
        from core.middleware import AtomicWritesMiddleware
        from core.models import Subscriber

        request = RequestFactory().post("/")

        def get_response(req):
            Subscriber.objects.create(email="rollback@example.com")
            got_request_exception.send(
                sender=self.__class__, request=req, exception=RuntimeError("boom")
            )
            return HttpResponse("ok")

        response = AtomicWritesMiddleware(get_response)(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subscriber.objects.count(), 0, "the failed POST must roll back")

    def test_successful_write_is_kept(self):
        from core.middleware import AtomicWritesMiddleware
        from core.models import Subscriber

        request = RequestFactory().post("/")

        def get_response(req):
            Subscriber.objects.create(email="kept@example.com")
            return HttpResponse("ok")

        AtomicWritesMiddleware(get_response)(request)
        self.assertEqual(Subscriber.objects.count(), 1)


class ContextProcessorTests(CartFixtureMixin, TestCase):
    def setUp(self):
        cache.clear()
        self.build_basket()

    def shop_context(self, request):
        from core.context_processors import shop

        return shop(request)

    def test_anonymous_session_cart_counts_lines(self):
        Cart.objects.filter(pk=self.cart_pk).update(user=None, session_key=ANON_SESSION_KEY)
        request = make_request(session_key=ANON_SESSION_KEY)
        ctx = self.shop_context(request)
        self.assertEqual(ctx["cart_count"], 3)
        self.assertEqual(ctx["wishlist_count"], 0)

    def test_anonymous_without_a_cart_counts_zero(self):
        ctx = self.shop_context(make_request(session_key=OTHER_SESSION_KEY))
        self.assertEqual(ctx["cart_count"], 0)
        self.assertEqual(ctx["wishlist_count"], 0)

    def test_authenticated_counts_badge_and_wishlist(self):
        Wishlist.objects.create(user=self.user, product=self.product)
        Wishlist.objects.create(user=self.user, product=self.sized_product)
        ctx = self.shop_context(make_request(user=self.user))
        self.assertEqual(ctx["cart_count"], 3)
        self.assertEqual(ctx["wishlist_count"], 2)

    def test_branding_values(self):
        from django.conf import settings

        ctx = self.shop_context(make_request())
        self.assertEqual(ctx["SITE_NAME"], settings.SITE_NAME)
        self.assertEqual(ctx["CURRENCY"], settings.CURRENCY)
        self.assertEqual(ctx["products_per_page"], settings.PRODUCTS_PER_PAGE)
        self.assertEqual(
            {c.name for c in ctx["nav_categories"]},
            {"Cat for Fern Pot", "Cat for Violet Pot"},
        )
        again = self.shop_context(make_request(session_key=OTHER_SESSION_KEY))
        self.assertEqual(
            {c.name for c in again["nav_categories"]},
            {"Cat for Fern Pot", "Cat for Violet Pot"},
        )


class AddressDefaultTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="addrfan", password="hunter2pass")
        self.other = User.objects.create_user(username="otherfan", password="hunter2pass")

    def make_address(self, user, **kwargs):
        from core.models import Address

        defaults = {"user": user, "full_name": "Jane Doe",
                    "line1": "Green Street 1", "city": "Kyiv"}
        defaults.update(kwargs)
        return Address.objects.create(**defaults)

    def test_second_default_clears_the_first(self):
        from core.models import Address

        first = self.make_address(self.user, is_default=True)
        second = self.make_address(self.user, is_default=True, line1="Other Street 2")
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)
        self.assertEqual(Address.objects.filter(user=self.user, is_default=True).count(), 1)

    def test_other_users_keep_their_defaults(self):
        from core.models import Address

        self.make_address(self.user, is_default=True)
        their_default = self.make_address(self.other, is_default=True, line1="Other Street 2")
        self.make_address(self.user, is_default=True, line1="Third Street 3")
        their_default.refresh_from_db()
        self.assertTrue(their_default.is_default)
        self.assertEqual(Address.objects.filter(user=self.other, is_default=True).count(), 1)

    def test_flipping_an_old_address_back_to_default(self):
        from core.models import Address

        first = self.make_address(self.user, is_default=True)
        second = self.make_address(self.user, is_default=True, line1="Other Street 2")
        first.is_default = True
        first.save()
        second.refresh_from_db()
        self.assertTrue(first.is_default)
        self.assertFalse(second.is_default)
        self.assertEqual(Address.objects.filter(user=self.user, is_default=True).count(), 1)
