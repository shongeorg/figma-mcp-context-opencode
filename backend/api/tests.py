from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from catalog.models import (
    Category,
    Product,
    ProductImage,
    ProductSize,
    Review,
    Size,
    Tag,
    Wishlist,
)
from core.models import Address, Subscriber
from orders.models import Cart, CartItem, Order

from .models import BlogPost

User = get_user_model()


def make_user(username="alice", password="secretpw", email=None, **kwargs):
    return User.objects.create_user(
        username=username,
        password=password,
        email=email or f"{username}@example.com",
        **kwargs,
    )


def make_staff_user(username="root", password="secretpw"):
    return make_user(username=username, password=password, role=User.Role.ADMIN)


def make_category(name="House Plants", slug=None, parent=None, ordering=0, **kwargs):
    return Category.objects.create(
        name=name, slug=slug, parent=parent, ordering=ordering, **kwargs
    )


def make_product(name="African Violet", category=None, price="19.99", stock=10, **kwargs):
    if category is None:
        category = make_category()
    return Product.objects.create(
        name=name, category=category, price=Decimal(price), stock=stock, **kwargs
    )


def make_size(name="S", ordering=0):
    return Size.objects.create(name=name, ordering=ordering)


def make_product_size(product, size, price_delta="0.00", stock=5, is_active=True):
    return ProductSize.objects.create(
        product=product,
        size=size,
        price_delta=Decimal(price_delta),
        stock=stock,
        is_active=is_active,
    )


def make_tag(name="Rare", **kwargs):
    return Tag.objects.create(name=name, **kwargs)


def make_review(product, user, rating=5, is_approved=True, title="Great", body="Lovely."):
    return Review.objects.create(
        product=product, user=user, rating=rating, title=title, body=body,
        is_approved=is_approved,
    )


def make_blog_post(title="Plant care 101", **kwargs):
    return BlogPost.objects.create(title=title, **kwargs)


def add_image(product, name="products/shot.jpg", primary=False, ordering=0):
    return ProductImage.objects.create(
        product=product, image=name, is_primary=primary, ordering=ordering
    )


def json_body(response):
    return json.loads(response.content.decode("utf-8"))


def post_json(client, url, data=None, **extra):
    return client.post(url, data=json.dumps(data or {}), content_type="application/json", **extra)


def patch_json(client, url, data=None, **extra):
    return client.patch(url, data=json.dumps(data or {}), content_type="application/json", **extra)


class ApiTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.category = make_category("House Plants", "house-plants")
        self.product = make_product("African Violet", self.category, price="19.99", stock=10)


class ProductsListTests(ApiTestCase):
    url = "/api/products/"

    def _many(self, count):
        return [
            make_product(f"Plant {index:02d}", self.category, price=str(5 + index * 5), stock=3)
            for index in range(count)
        ]

    def test_pagination_meta(self):
        self._many(12)
        response = self.client.get(self.url, {"limit": 5})
        data = json_body(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["products"]), 5)
        self.assertEqual(data["meta"]["limit"], 5)
        self.assertEqual(data["meta"]["offset"], 0)
        self.assertEqual(data["meta"]["count"], 13)
        self.assertIn("offset=5", data["meta"]["next"])

    def test_pagination_offset_tail_and_no_next(self):
        self._many(12)
        data = json_body(self.client.get(self.url, {"limit": 5, "offset": 10}))

        self.assertEqual(len(data["products"]), 3)
        self.assertEqual(data["meta"]["offset"], 10)
        self.assertIsNone(data["meta"]["next"])

    def test_default_limit_is_nine(self):
        self._many(12)
        data = json_body(self.client.get(self.url))
        self.assertEqual(len(data["products"]), 9)

    def test_limit_is_capped_at_fifty(self):
        self._many(3)
        data = json_body(self.client.get(self.url, {"limit": 999}))
        self.assertEqual(data["meta"]["limit"], 50)

    def test_bad_limit_or_offset_is_a_400(self):
        response = self.client.get(self.url, {"limit": "many"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("limit", json_body(response)["errors"]["detail"].lower())

        response = self.client.get(self.url, {"offset": -3})
        self.assertEqual(response.status_code, 400)

    def test_category_filter_includes_descendants(self):
        child = make_category("Carnivorous", "carnivorous", parent=self.category, ordering=1)
        grandchild = make_category("Venus Flytrap", "venus-flytrap", parent=child, ordering=1)
        other = make_category("Garden Tools", "garden-tools")
        make_product("Venus Plant", grandchild)
        make_product("Trowel", other)

        data = json_body(self.client.get(self.url, {"category": "house-plants"}))
        self.assertEqual(data["meta"]["count"], 2)

        data = json_body(self.client.get(self.url, {"category": "carnivorous"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["name"], "Venus Plant")

    def test_unknown_category_is_404(self):
        response = self.client.get(self.url, {"category": "nope"})
        self.assertEqual(response.status_code, 404)

    def test_inactive_category_filter_is_404(self):
        make_category("Hidden", "hidden", is_active=False)
        response = self.client.get(self.url, {"category": "hidden"})
        self.assertEqual(response.status_code, 404)

    def test_size_filter_ignores_inactive_size_rows(self):
        small = make_size("S", ordering=1)
        medium = make_size("M", ordering=2)
        other = make_product("Snake Plant", self.category, price="9.99")
        make_product_size(self.product, small, is_active=True)
        make_product_size(other, small, is_active=False)
        make_product_size(other, medium, is_active=True)

        data = json_body(self.client.get(self.url, {"size": "s"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["slug"], self.product.slug)

        data = json_body(self.client.get(self.url, {"size": "s,m"}))
        self.assertEqual(data["meta"]["count"], 2)

    def test_tag_filter(self):
        rare = make_tag("Rare")
        hidden = make_tag("Hidden", is_active=False)
        self.product.tags.add(rare)
        other = make_product("Fern", self.category, price="7.99")
        other.tags.add(hidden)

        data = json_body(self.client.get(self.url, {"tag": "rare"}))
        self.assertEqual(data["meta"]["count"], 1)

        data = json_body(self.client.get(self.url, {"tag": "hidden"}))
        self.assertEqual(data["meta"]["count"], 0)

    def test_price_min_max(self):
        make_product("Mid", self.category, price="20.00")
        make_product("High", self.category, price="30.00")

        data = json_body(self.client.get(self.url, {"price_min": "15"}))
        self.assertEqual(data["meta"]["count"], 3)

        data = json_body(self.client.get(self.url, {"price_max": "15"}))
        self.assertEqual(data["meta"]["count"], 0)

        data = json_body(self.client.get(self.url, {"price_min": "25", "price_max": "35"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["name"], "High")

    def test_invalid_price_is_400(self):
        response = self.client.get(self.url, {"price_min": "abc"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("price_min", json_body(response)["errors"])

    def test_sale_filter(self):
        make_product("Sale Item", self.category, price="20.00", old_price=Decimal("30.00"))
        data = json_body(self.client.get(self.url, {"sale": "1"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["name"], "Sale Item")
        self.assertTrue(data["products"][0]["is_on_sale"])
        self.assertEqual(data["products"][0]["old_price"], "30.00")
        self.assertEqual(data["products"][0]["discount_percent"], 33)

    def test_featured_filter(self):
        self.product.is_featured = True
        self.product.save(update_fields=["is_featured"])
        make_product("Regular", self.category, price="5.00")

        data = json_body(self.client.get(self.url, {"featured": "true"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["slug"], self.product.slug)

    def test_search_by_name_and_description(self):
        make_product("Snake Plant", self.category, price="12.00",
                     description="A hardy succulent from Africa")
        data = json_body(self.client.get(self.url, {"q": "violet"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["name"], "African Violet")

        data = json_body(self.client.get(self.url, {"q": "succulent"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["name"], "Snake Plant")

    def test_sort_price_ascending_and_descending(self):
        make_product("Cheap", self.category, price="5.00")
        make_product("Pricey", self.category, price="90.00")

        names = [p["name"] for p in json_body(
            self.client.get(self.url, {"sort": "price-asc", "limit": 50})
        )["products"]]
        self.assertEqual(names, ["Cheap", "African Violet", "Pricey"])

        names = [p["name"] for p in json_body(
            self.client.get(self.url, {"sort": "price-desc", "limit": 50})
        )["products"]]
        self.assertEqual(names, ["Pricey", "African Violet", "Cheap"])

    def test_sort_name_and_rating_and_newest(self):
        alpha = make_product("Alpha", self.category, price="30.00")
        make_product("Gamma", self.category, price="10.00")
        for product, rating in ((self.product, 3), (alpha, 5)):
            product.rating = Decimal(rating)
            product.save(update_fields=["rating"])

        names = [p["name"] for p in json_body(
            self.client.get(self.url, {"sort": "name", "limit": 50})
        )["products"]]
        self.assertEqual(names, ["African Violet", "Alpha", "Gamma"])

        rated = [p["name"] for p in json_body(
            self.client.get(self.url, {"sort": "rating", "limit": 50})
        )["products"]]
        self.assertEqual(rated[0], "Alpha")

        Product.objects.filter(name="Gamma").update(
            created_at=timezone.now() + timedelta(days=1)
        )
        newest = [p["name"] for p in json_body(
            self.client.get(self.url, {"sort": "newest", "limit": 50})
        )["products"]]
        self.assertEqual(newest[0], "Gamma")

    def test_unknown_sort_falls_back_to_default(self):
        make_product("Another", self.category, price="25.00")
        data = json_body(self.client.get(self.url, {"sort": "bogus", "limit": 50}))
        self.assertEqual(data["meta"]["count"], 2)

    def test_disabled_products_hidden_from_anonymous(self):
        make_product("Retired", self.category, price="15.00", is_active=False)
        data = json_body(self.client.get(self.url, {"limit": 50}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["products"][0]["name"], "African Violet")

        data = json_body(self.client.get(self.url, {"include_disabled": "1", "limit": 50}))
        self.assertEqual(data["meta"]["count"], 1)

    def test_staff_can_include_disabled(self):
        make_product("Retired", self.category, price="15.00", is_active=False)
        staff = make_staff_user()
        self.client.force_login(staff)

        data = json_body(self.client.get(self.url, {"include_disabled": "1", "limit": 50}))
        self.assertEqual(data["meta"]["count"], 2)

    def test_product_row_shape(self):
        add_image(self.product, "products/violet.jpg", primary=True)
        tag = make_tag("Best")
        self.product.tags.add(tag)

        row = json_body(self.client.get(self.url))["products"][0]
        for key in ("id", "name", "slug", "sku", "category", "price", "old_price",
                    "is_on_sale", "discount_percent", "stock", "is_featured",
                    "is_new", "rating", "reviews_count", "image", "tags"):
            self.assertIn(key, row)
        self.assertEqual(row["category"]["slug"], "house-plants")
        self.assertEqual(row["image"], "/media/products/violet.jpg")
        self.assertEqual(row["tags"], ["best"])
        self.assertEqual(row["price"], "19.99")
        self.assertEqual(row["rating"], "0.00")

    def test_write_methods_rejected(self):
        self.assertEqual(post_json(self.client, self.url).status_code, 405)


class ProductDetailTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.small = make_size("S", ordering=1)
        self.large = make_size("L", ordering=2)
        make_product_size(self.product, self.small, price_delta="2.50", stock=4)
        make_product_size(self.product, self.large, is_active=False)
        self.product.tags.add(make_tag("Best"))
        add_image(self.product, "products/one.jpg", primary=True)
        add_image(self.product, "products/two.jpg", ordering=1)

        self.reviewer = make_user("reviewer")
        self.fan = make_user("fan")
        self.pending_author = make_user("pendingAuthor")
        make_review(self.product, self.reviewer, rating=5)
        make_review(self.product, self.fan, rating=4)
        make_review(self.product, self.pending_author, rating=1, is_approved=False)

    def url(self, slug=None):
        return f"/api/products/{slug or self.product.slug}/"

    def test_detail_shape(self):
        response = self.client.get(self.url())
        data = json_body(response)

        self.assertEqual(response.status_code, 200)
        product = data["product"]
        for key in ("category", "sizes", "tags", "images", "reviews", "description",
                    "short_description", "price", "rating", "reviews_count"):
            self.assertIn(key, product)

        self.assertEqual(product["category"]["name"], "House Plants")
        self.assertEqual(product["category"]["parent"], None)
        self.assertEqual(product["tags"], ["best"])

        self.assertEqual(len(product["sizes"]), 1)
        self.assertEqual(product["sizes"][0]["size"]["name"], "S")
        self.assertEqual(product["sizes"][0]["price"], "22.49")

        self.assertEqual(len(product["images"]), 2)
        self.assertEqual(product["images"][0]["is_primary"], True)
        self.assertEqual(product["images"][0]["url"], "/media/products/one.jpg")

        self.assertEqual(len(product["reviews"]), 2)
        self.assertEqual(product["reviews"][0]["rating"], 4)
        self.assertNotIn("product", product["reviews"][0])

    def test_staff_sees_pending_reviews_and_disabled_product(self):
        staff = make_staff_user()
        self.client.force_login(staff)
        product = json_body(self.client.get(self.url()))["product"]
        self.assertEqual(len(product["reviews"]), 3)

        disabled = make_product("Retired", self.category, price="5.00", is_active=False)
        self.assertEqual(self.client.get(self.url(disabled.slug)).status_code, 200)

    def test_missing_and_disabled_are_404_for_anonymous(self):
        self.assertEqual(self.client.get(self.url("no-such-plant")).status_code, 404)
        disabled = make_product("Retired", self.category, price="5.00", is_active=False)
        self.assertEqual(self.client.get(self.url(disabled.slug)).status_code, 404)

    def test_nested_category_parent(self):
        child = make_category("Carnivorous", "carnivorous", parent=self.category)
        product = make_product("Venus", child, price="30.00")
        row = json_body(self.client.get(self.url(product.slug)))["product"]
        self.assertEqual(row["category"]["slug"], "carnivorous")
        self.assertEqual(row["category"]["parent"]["slug"], "house-plants")


class SizesAndTagsTests(ApiTestCase):
    def test_sizes_ordered_with_counts(self):
        make_size("L", ordering=3)
        medium = make_size("M", ordering=1)
        small = make_size("S", ordering=2)
        make_product_size(self.product, small)
        retired = make_product("Retired", self.category, price="5.00", is_active=False)
        make_product_size(retired, medium)

        data = json_body(self.client.get("/api/sizes/"))
        names = [row["name"] for row in data["sizes"]]
        self.assertEqual(names, ["M", "S", "L"])
        counts = {row["name"]: row["product_count"] for row in data["sizes"]}
        self.assertEqual(counts, {"M": 0, "S": 1, "L": 0})

    def test_tags_active_only_alphabetical(self):
        make_tag("Zebra")
        make_tag("Care")
        make_tag("Hidden", is_active=False)

        data = json_body(self.client.get("/api/tags/"))
        self.assertEqual([row["name"] for row in data["tags"]], ["Care", "Zebra"])
        self.assertEqual(sorted(data["tags"][0].keys()), ["id", "name", "slug"])


class CategoryTreeTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.herbs = make_category("Herbs", "herbs", parent=self.category, ordering=1)
        self.carnivorous = make_category("Carnivorous", "carnivorous", parent=self.category, ordering=2)
        make_product("Basil", self.herbs, price="4.00")
        make_product("Flytrap", self.carnivorous, price="25.00")
        make_product("Retired Flytrap", self.carnivorous, price="25.00", is_active=False)

    def test_tree_shape_and_counts(self):
        data = json_body(self.client.get("/api/categories/"))
        roots = data["categories"]

        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root["slug"], "house-plants")
        self.assertEqual(root["product_count"], 3)
        self.assertEqual([c["slug"] for c in root["children"]], ["herbs", "carnivorous"])
        self.assertEqual(root["children"][0]["product_count"], 1)
        self.assertEqual(root["children"][1]["product_count"], 1)
        self.assertEqual(root["children"][0]["children"], [])

    def test_inactive_categories_hidden_with_their_subtree(self):
        seeds = make_category("Seeds", "seeds", is_active=False)
        make_category("Sunflower", "sunflower", parent=seeds)
        make_product("Sunflower Seeds", seeds, price="3.00")

        data = json_body(self.client.get("/api/categories/"))
        slugs = [c["slug"] for c in data["categories"]]
        self.assertEqual(slugs, ["house-plants"])
        self.assertNotIn("seeds", json.dumps(data))


class BlogTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.post = make_blog_post("Care basics", tags=["care"], body="Water weekly.")
        make_blog_post("Indoor jungle", tags=["care", "indoor"])
        make_blog_post("Photo dump", tags=[])
        self.draft = make_blog_post("Unfinished thoughts", is_published=False)
        self.scheduled = make_blog_post(
            "Next week", is_published=True,
            published_at=timezone.now() + timedelta(days=7),
        )

    def test_list_published_only(self):
        data = json_body(self.client.get("/api/blog/"))
        self.assertEqual(data["meta"]["count"], 3)
        self.assertEqual(data["posts"][0]["title"], "Photo dump")

    def test_pagination(self):
        data = json_body(self.client.get("/api/blog/", {"limit": 2}))
        self.assertEqual(len(data["posts"]), 2)
        self.assertEqual(data["meta"]["count"], 3)
        self.assertIn("offset=2", data["meta"]["next"])

    def test_search(self):
        data = json_body(self.client.get("/api/blog/", {"q": "jungle"}))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["posts"][0]["slug"], "indoor-jungle")

    def test_tag_filter(self):
        data = json_body(self.client.get("/api/blog/", {"tag": "care"}))
        self.assertEqual(data["meta"]["count"], 2)
        data = json_body(self.client.get("/api/blog/", {"tag": "indoor"}))
        self.assertEqual(data["meta"]["count"], 1)

    def test_detail_404_for_draft_unknown_and_scheduled(self):
        self.assertEqual(self.client.get(f"/api/blog/{self.post.slug}/").status_code, 200)
        self.assertEqual(self.client.get("/api/blog/nope/").status_code, 404)
        self.assertEqual(
            self.client.get(f"/api/blog/{self.draft.slug}/").status_code, 404
        )
        self.assertEqual(
            self.client.get(f"/api/blog/{self.scheduled.slug}/").status_code, 404
        )

    def test_staff_previews_drafts(self):
        self.client.force_login(make_staff_user())
        response = self.client.get(f"/api/blog/{self.draft.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(json_body(response)["post"]["is_published"])


class CartTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.small = make_size("S", ordering=1)
        self.size_row = make_product_size(
            self.product, self.small, price_delta="2.50", stock=5
        )
        self.other = make_product("Snake Plant", self.category, price="30.00", stock=10)

    def add(self, product=None, **extra):
        value = product or self.product
        payload = {
            "product": value if isinstance(value, int) else value.slug,
            "quantity": 1,
        }
        payload.update(extra)
        return post_json(self.client, "/api/cart/items/", payload)

    def test_get_creates_empty_cart_for_anonymous_session(self):
        response = self.client.get("/api/cart/")
        data = json_body(response)

        self.assertEqual(response.status_code, 200)
        cart = data["cart"]
        self.assertEqual(cart["item_count"], 0)
        self.assertEqual(cart["subtotal"], "0.00")
        self.assertEqual(cart["discount"], "0.00")
        self.assertEqual(cart["shipping"], "0.00")
        self.assertEqual(cart["total"], "0.00")
        self.assertIsNone(cart["coupon_code"])
        self.assertEqual(cart["items"], [])
        self.assertEqual(cart["free_shipping_threshold"], "120.00")

        row = Cart.objects.get()
        self.assertIsNotNone(row.session_key)
        self.assertIsNone(row.user)

    def test_add_item_and_totals(self):
        response = self.add(quantity=2)
        data = json_body(response)

        self.assertEqual(response.status_code, 201)
        cart = data["cart"]
        self.assertEqual(cart["item_count"], 2)
        self.assertEqual(cart["subtotal"], "39.98")
        self.assertEqual(cart["shipping"], "9.00")
        self.assertEqual(cart["total"], "48.98")
        line = cart["items"][0]
        self.assertEqual(line["quantity"], 2)
        self.assertEqual(line["unit_price"], "19.99")
        self.assertEqual(line["line_total"], "39.98")
        self.assertIsNone(line["size"])
        self.assertEqual(line["product"]["slug"], self.product.slug)

    def test_add_item_with_size_uses_price_delta(self):
        response = self.add(size=self.size_row.pk)
        cart = json_body(response)["cart"]
        line = cart["items"][0]
        self.assertEqual(line["unit_price"], "22.49")
        self.assertEqual(line["size"]["name"], "S")
        self.assertEqual(cart["subtotal"], "22.49")

    def test_add_twice_merges_the_line(self):
        self.add()
        self.add()
        self.assertEqual(CartItem.objects.count(), 1)
        cart = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertEqual(cart["items"][0]["quantity"], 2)

    def test_add_by_product_id(self):
        response = self.add(product=self.product.pk)
        self.assertEqual(response.status_code, 201)

    def test_add_missing_product_error_shape(self):
        response = post_json(self.client, "/api/cart/items/", {})
        data = json_body(response)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"errors": {"product": ["This field is required."]}})

    def test_add_unknown_product_error_shape(self):
        response = post_json(self.client, "/api/cart/items/", {"product": "nope"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_body(response), {"errors": {"product": ["Unknown product."]}})

    def test_add_disabled_product_is_400(self):
        retired = make_product("Retired", self.category, price="5.00", is_active=False)
        response = self.add(product=retired)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json_body(response),
            {"errors": {"product": ["This product is no longer for sale."]}},
        )

    def test_add_size_not_offered_is_400(self):
        other_size = make_product_size(self.other, make_size("M", ordering=9))
        response = self.add(size=other_size.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn("size", json_body(response)["errors"])

    def test_add_inactive_size_is_400(self):
        retired = make_product_size(
            self.product, make_size("L", ordering=5), is_active=False
        )
        response = self.add(size=retired.pk)
        self.assertEqual(response.status_code, 400)
        self.assertIn("size", json_body(response)["errors"])

    def test_add_insufficient_stock_is_400(self):
        response = self.add(quantity=11)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json_body(response), {"errors": {"quantity": ["Only 10 left in stock."]}}
        )

    def test_add_size_stock_is_enforced(self):
        response = self.add(size=self.size_row.pk, quantity=6)
        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", json_body(response)["errors"])

    def test_add_bad_quantity_is_400(self):
        for bad in (0, -2, "lots"):
            response = self.add(quantity=bad)
            self.assertEqual(response.status_code, 400, bad)
            self.assertIn("quantity", json_body(response)["errors"])

    def test_patch_quantity_updates_totals(self):
        self.add(quantity=1)
        line_id = json_body(self.client.get("/api/cart/"))["cart"]["items"][0]["id"]

        response = patch_json(
            self.client, f"/api/cart/items/{line_id}/", {"quantity": 5}
        )
        self.assertEqual(response.status_code, 200)
        cart = json_body(response)["cart"]
        self.assertEqual(cart["items"][0]["quantity"], 5)
        self.assertEqual(cart["subtotal"], "99.95")

    def test_patch_quantity_zero_deletes_the_line(self):
        self.add()
        line_id = json_body(self.client.get("/api/cart/"))["cart"]["items"][0]["id"]
        response = patch_json(
            self.client, f"/api/cart/items/{line_id}/", {"quantity": 0}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response)["cart"]["items"], [])
        self.assertEqual(CartItem.objects.count(), 0)

    def test_patch_over_stock_is_400(self):
        self.add()
        line_id = json_body(self.client.get("/api/cart/"))["cart"]["items"][0]["id"]
        response = patch_json(
            self.client, f"/api/cart/items/{line_id}/", {"quantity": 50}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", json_body(response)["errors"])

    def test_patch_unknown_or_foreign_line_is_404(self):
        self.add()
        line_id = json_body(self.client.get("/api/cart/"))["cart"]["items"][0]["id"]
        self.assertEqual(
            patch_json(self.client, "/api/cart/items/9999/", {"quantity": 2}).status_code,
            404,
        )
        self.client.logout()
        make_user("mallory", "mallorypw")
        self.client.login(username="mallory", password="mallorypw")
        self.assertEqual(
            patch_json(self.client, f"/api/cart/items/{line_id}/", {"quantity": 2}).status_code,
            404,
        )

    def test_delete_line(self):
        self.add()
        line_id = json_body(self.client.get("/api/cart/"))["cart"]["items"][0]["id"]
        response = self.client.delete(f"/api/cart/items/{line_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response)["cart"]["item_count"], 0)
        self.assertEqual(
            self.client.delete("/api/cart/items/424242/").status_code, 404
        )

    def test_coupon_green10_applies_ten_percent(self):
        self.add(product=self.other, quantity=1)
        post_json(self.client, "/api/cart/items/",
                  {"product": self.other.slug, "quantity": 1})

        response = patch_json(self.client, "/api/cart/coupon/", {"code": "green10"})
        self.assertEqual(response.status_code, 200)
        cart = json_body(response)["cart"]
        self.assertEqual(cart["coupon_code"], "GREEN10")
        self.assertEqual(cart["subtotal"], "60.00")
        self.assertEqual(cart["discount"], "6.00")
        self.assertEqual(cart["shipping"], "9.00")
        self.assertEqual(cart["total"], "63.00")

    def test_coupon_invalid_is_400_with_shape(self):
        self.add()
        response = patch_json(self.client, "/api/cart/coupon/", {"code": "NOPE10"})
        self.assertEqual(response.status_code, 400)
        errors = json_body(response)["errors"]
        self.assertIn("code", errors)
        self.assertIn("not a valid coupon", errors["code"][0])
        cart = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertIsNone(cart["coupon_code"])
        self.assertEqual(cart["discount"], "0.00")

    def test_coupon_empty_code_clears_the_discount(self):
        self.add(product=self.other, quantity=2)
        patch_json(self.client, "/api/cart/coupon/", {"code": "GREEN10"})
        response = patch_json(self.client, "/api/cart/coupon/", {"code": ""})
        self.assertEqual(response.status_code, 200)
        cart = json_body(response)["cart"]
        self.assertIsNone(cart["coupon_code"])
        self.assertEqual(cart["discount"], "0.00")

    def test_clear_endpoint(self):
        self.add()
        response = self.client.delete("/api/cart/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response)["cart"]["item_count"], 0)
        self.assertEqual(CartItem.objects.count(), 0)
        cart = Cart.objects.get()
        self.assertEqual(cart.coupon_code, "")
        self.assertEqual(self.client.delete("/api/cart/").status_code, 200)
        self.assertEqual(self.client_class().delete("/api/cart/").status_code, 404)

    def test_shipping_flat_below_threshold(self):
        self.add(product=self.other, quantity=1)
        cart = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertEqual(cart["shipping"], "9.00")
        self.assertEqual(cart["total"], "39.00")

    def test_shipping_free_at_threshold(self):
        self.add(product=self.other, quantity=4)
        cart = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertEqual(cart["subtotal"], "120.00")
        self.assertEqual(cart["shipping"], "0.00")
        self.assertEqual(cart["total"], "120.00")

    def test_shipping_is_computed_on_the_discounted_subtotal(self):
        self.add(product=self.other, quantity=1)
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 5})
        cart = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertEqual(cart["subtotal"], "129.95")
        self.assertEqual(cart["shipping"], "0.00")

        patch_json(self.client, "/api/cart/coupon/", {"code": "GREEN10"})
        cart = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertEqual(cart["discount"], "13.00")
        self.assertEqual(cart["shipping"], "9.00")
        self.assertEqual(cart["total"], "125.95")

    def test_cart_is_per_session(self):
        self.add()
        other_client = self.client_class()
        data = json_body(other_client.get("/api/cart/"))
        self.assertEqual(data["cart"]["item_count"], 0)

    def test_wrong_methods_are_405(self):
        self.assertEqual(self.client.get("/api/cart/items/").status_code, 405)
        self.assertEqual(post_json(self.client, "/api/cart/").status_code, 405)


class CheckoutTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("bob", "bobpw")
        self.client.force_login(self.user)
        self.small = make_size("S", ordering=1)
        self.size_row = make_product_size(self.product, self.small, stock=6)

    def form(self, **overrides):
        data = {
            "full_name": "Bob Smith",
            "email": "bob@example.com",
            "phone": "+380671112233",
            "address_line": "Khreshchatyk 1",
            "city": "Kyiv",
            "region": "Kyivska",
            "postal_code": "01001",
            "country": "Ukraine",
            "note": "Ring the bell",
            "payment_method": "cod",
        }
        data.update(overrides)
        return data

    def checkout(self, **overrides):
        return post_json(self.client, "/api/checkout/", self.form(**overrides))

    def test_anonymous_is_401(self):
        self.client.logout()
        response = post_json(self.client, "/api/checkout/", self.form())
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", json_body(response))

    def test_empty_cart_is_400(self):
        response = self.checkout()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json_body(response), {"errors": {"cart": ["Your basket is empty."]}}
        )

    def test_invalid_form_is_400_with_field_errors(self):
        post_json(self.client, "/api/cart/items/", {"product": self.product.slug})
        response = self.checkout(email="", payment_method="bitcoin")
        self.assertEqual(response.status_code, 400)
        errors = json_body(response)["errors"]
        self.assertIn("email", errors)
        self.assertIn("payment_method", errors)

    def test_success_creates_order_decrements_stock_and_clears_cart(self):
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 2})
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "size": self.size_row.pk, "quantity": 3})

        response = self.checkout()
        self.assertEqual(response.status_code, 201)

        payload = json_body(response)["order"]
        order = Order.objects.get()
        self.assertEqual(payload["number"], order.number)
        self.assertTrue(order.number.startswith("GS-"))
        self.assertEqual(payload["status"], "new")
        self.assertEqual(payload["subtotal"], "99.95")
        self.assertEqual(payload["discount"], "0.00")
        self.assertEqual(payload["shipping"], "9.00")
        self.assertEqual(payload["total"], "108.95")
        self.assertEqual(payload["items_count"], 5)
        self.assertEqual(len(payload["items"]), 2)

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.city, "Kyiv")
        self.assertEqual(order.payment_method, "cod")

        self.product.refresh_from_db()
        self.size_row.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(self.size_row.stock, 3)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_order_items_are_snapshots(self):
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 1})
        self.checkout()
        item = Order.objects.get().items.get()
        self.assertEqual(item.product_name, "African Violet")
        self.assertEqual(item.product_slug, self.product.slug)
        self.assertEqual(item.unit_price, Decimal("19.99"))

    def test_coupon_flows_into_order_totals(self):
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 1})
        patch_json(self.client, "/api/cart/coupon/", {"code": "GREEN10"})

        response = self.checkout()
        payload = json_body(response)["order"]
        self.assertEqual(payload["discount"], "2.00")
        self.assertEqual(payload["coupon_code"], "GREEN10")
        self.assertEqual(payload["shipping"], "9.00")
        self.assertEqual(payload["total"], "26.99")

    def test_default_address_adoption(self):
        address = Address.objects.create(
            user=self.user, label="home", full_name="Bob Smith",
            phone="+380671112233", line1="Bankova 2", city="Kyiv",
            country="Ukraine", is_default=True,
        )
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 1})

        response = post_json(
            self.client, "/api/checkout/",
            {"email": "bob@example.com", "payment_method": "cod", "address_id": address.pk},
        )
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get()
        self.assertEqual(order.address_line, "Bankova 2")
        self.assertEqual(order.city, "Kyiv")
        self.assertEqual(order.full_name, "Bob Smith")
        self.assertEqual(order.country, "Ukraine")

    def test_posted_values_override_the_adopted_address(self):
        address = Address.objects.create(
            user=self.user, full_name="Bob Smith", line1="Bankova 2", city="Kyiv",
            country="Ukraine", is_default=True,
        )
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 1})

        response = post_json(
            self.client, "/api/checkout/",
            {"email": "bob@example.com", "payment_method": "cod",
             "address_id": address.pk, "city": "Lviv"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.get().city, "Lviv")

    def test_foreign_address_is_400(self):
        stranger = make_user("eve", "evepw")
        address = Address.objects.create(
            user=stranger, full_name="Eve", line1="Nowhere", city="Odesa",
        )
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 1})
        response = post_json(
            self.client, "/api/checkout/",
            {**self.form(), "address_id": address.pk},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("address_id", json_body(response)["errors"])


class OrdersTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user("alice", "alicepw")
        self.bob = make_user("bob", "bobpw")
        self.staff = make_staff_user()
        self.order_alice = Order.objects.create(
            user=self.alice, full_name="Alice", email="alice@example.com",
            address_line="Shevchenka 1", city="Lviv",
            subtotal=Decimal("19.99"), total=Decimal("28.99"),
        )
        self.order_bob = Order.objects.create(
            user=self.bob, full_name="Bob", email="bob@example.com",
            address_line="Franka 2", city="Kyiv",
            subtotal=Decimal("5.00"), total=Decimal("14.00"),
        )

    def test_anonymous_is_401(self):
        self.assertEqual(self.client.get("/api/orders/").status_code, 401)
        self.assertEqual(
            self.client.get(f"/api/orders/{self.order_alice.number}/").status_code, 401
        )

    def test_list_returns_only_own_orders(self):
        self.client.force_login(self.alice)
        data = json_body(self.client.get("/api/orders/"))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["orders"][0]["number"], self.order_alice.number)
        self.assertEqual(data["orders"][0]["status"], "new")
        self.assertIn("items", data["orders"][0])

    def test_staff_sees_all_with_all_param(self):
        self.client.force_login(self.staff)
        data = json_body(self.client.get("/api/orders/?all=1"))
        self.assertEqual(data["meta"]["count"], 2)
        data = json_body(self.client.get("/api/orders/"))
        self.assertEqual(data["meta"]["count"], 0)

    def test_status_filter_is_staff_only(self):
        self.client.force_login(self.alice)
        response = self.client.get("/api/orders/?status=new")
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.staff)
        data = json_body(self.client.get("/api/orders/?all=1&status=new"))
        self.assertEqual(data["meta"]["count"], 2)
        self.order_bob.transition(Order.Status.SHIPPED)
        data = json_body(self.client.get("/api/orders/?all=1&status=new"))
        self.assertEqual(data["meta"]["count"], 1)

        response = self.client.get("/api/orders/?all=1&status=bogus")
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", json_body(response)["errors"])

    def test_detail_permissions(self):
        self.client.force_login(self.alice)
        response = self.client.get(f"/api/orders/{self.order_alice.number}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response)["order"]["full_name"], "Alice")

        self.assertEqual(
            self.client.get(f"/api/orders/{self.order_bob.number}/").status_code, 404
        )
        self.assertEqual(self.client.get("/api/orders/GS-000000-DEAD/").status_code, 404)

        self.client.force_login(self.staff)
        self.assertEqual(
            self.client.get(f"/api/orders/{self.order_bob.number}/").status_code, 200
        )

    def test_owner_can_cancel_only_a_new_order(self):
        self.client.force_login(self.alice)
        response = patch_json(
            self.client, f"/api/orders/{self.order_alice.number}/", {"status": "cancelled"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response)["order"]["status"], "cancelled")

        self.order_alice.refresh_from_db()
        response = patch_json(
            self.client, f"/api/orders/{self.order_alice.number}/", {"status": "confirmed"}
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_cannot_advance_the_pipeline(self):
        self.client.force_login(self.alice)
        response = patch_json(
            self.client, f"/api/orders/{self.order_alice.number}/", {"status": "shipped"}
        )
        self.assertEqual(response.status_code, 403)
        self.order_alice.refresh_from_db()
        self.assertEqual(self.order_alice.status, "new")

    def test_staff_transitions_stamp_timestamps(self):
        self.client.force_login(self.staff)
        number = self.order_alice.number

        response = patch_json(self.client, f"/api/orders/{number}/", {"status": "confirmed"})
        self.assertEqual(response.status_code, 200)
        self.order_alice.refresh_from_db()
        self.assertIsNotNone(self.order_alice.processed_at)

        response = patch_json(self.client, f"/api/orders/{number}/", {"status": "shipped"})
        self.assertEqual(response.status_code, 200)
        self.order_alice.refresh_from_db()
        self.assertEqual(self.order_alice.status, "shipped")
        self.assertIsNotNone(self.order_alice.shipped_at)

    def test_invalid_status_and_unknown_order(self):
        self.client.force_login(self.alice)
        response = patch_json(
            self.client, f"/api/orders/{self.order_alice.number}/", {"status": "teleported"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("status", json_body(response)["errors"])

        response = patch_json(self.client, "/api/orders/GS-000000-0000/", {"status": "cancelled"})
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.bob)
        response = patch_json(
            self.client, f"/api/orders/{self.order_alice.number}/", {"status": "cancelled"}
        )
        self.assertEqual(response.status_code, 404)


class ReviewsTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user("alice", "alicepw")
        self.bob = make_user("bob", "bobpw")
        self.staff = make_staff_user()
        self.other = make_product("Snake Plant", self.category, price="9.99")
        self.approved = make_review(self.product, self.bob, rating=5, is_approved=True)
        self.pending = make_review(self.product, self.alice, rating=3, is_approved=False)

    def test_anonymous_sees_only_approved(self):
        data = json_body(self.client.get("/api/reviews/"))
        self.assertEqual(data["meta"]["count"], 1)
        self.assertEqual(data["reviews"][0]["id"], self.approved.pk)
        self.assertEqual(data["reviews"][0]["user"]["username"], "bob")
        self.assertEqual(data["reviews"][0]["product"]["slug"], self.product.slug)

    def test_filter_by_product(self):
        make_review(self.other, self.bob, rating=4)
        data = json_body(self.client.get(f"/api/reviews/?product={self.product.slug}"))
        self.assertEqual(data["meta"]["count"], 1)
        data = json_body(self.client.get(f"/api/reviews/?product={self.other.slug}"))
        self.assertEqual(data["meta"]["count"], 1)
        response = self.client.get("/api/reviews/?product=ghost")
        self.assertEqual(response.status_code, 400)
        self.assertIn("product", json_body(response)["errors"])

    def test_author_sees_their_own_pending_review(self):
        self.client.force_login(self.alice)
        data = json_body(self.client.get("/api/reviews/"))
        ids = {row["id"] for row in data["reviews"]}
        self.assertEqual(ids, {self.approved.pk, self.pending.pk})

    def test_staff_sees_everything(self):
        self.client.force_login(self.staff)
        data = json_body(self.client.get("/api/reviews/"))
        self.assertEqual(data["meta"]["count"], 2)

    def test_create_returns_201_pending(self):
        self.client.force_login(self.alice)
        response = post_json(
            self.client, "/api/reviews/",
            {"product": self.other.slug, "rating": 4, "title": "Nice", "body": "Very."},
        )
        self.assertEqual(response.status_code, 201)
        review = json_body(response)["review"]
        self.assertFalse(review["is_approved"])
        self.assertEqual(review["user"]["username"], "alice")
        self.assertEqual(review["rating"], 4)
        self.assertTrue(
            Review.objects.filter(user=self.alice, product=self.other, is_approved=False).exists()
        )

    def test_duplicate_review_is_400(self):
        self.client.force_login(self.bob)
        response = post_json(
            self.client, "/api/reviews/",
            {"product": self.product.slug, "rating": 2},
        )
        self.assertEqual(response.status_code, 400)
        errors = json_body(response)["errors"]
        self.assertIn("already reviewed", errors["product"][0])

    def test_anonymous_create_is_401(self):
        response = post_json(
            self.client, "/api/reviews/",
            {"product": self.product.slug, "rating": 5},
        )
        self.assertEqual(response.status_code, 401)

    def test_rating_bounds(self):
        self.client.force_login(self.alice)
        for bad in (0, 6, -1, "sparkling"):
            response = post_json(
                self.client, "/api/reviews/",
                {"product": self.product.slug, "rating": bad},
            )
            self.assertEqual(response.status_code, 400, bad)
            self.assertIn("rating", json_body(response)["errors"])

    def test_missing_or_unknown_product_is_400(self):
        self.client.force_login(self.alice)
        response = post_json(self.client, "/api/reviews/", {"rating": 3})
        self.assertEqual(response.status_code, 400)
        self.assertIn("product", json_body(response)["errors"])

        response = post_json(
            self.client, "/api/reviews/", {"product": "ghost", "rating": 3}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_body(response), {"errors": {"product": ["Unknown product."]}})

    def test_review_on_disabled_product_is_rejected(self):
        retired = make_product("Retired", self.category, price="5.00", is_active=False)
        self.client.force_login(self.alice)
        response = post_json(
            self.client, "/api/reviews/", {"product": retired.slug, "rating": 3}
        )
        self.assertEqual(response.status_code, 400)


class WishlistTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user("alice", "alicepw")
        self.other = make_product("Snake Plant", self.category, price="9.99")

    def test_requires_login(self):
        self.assertEqual(self.client.get("/api/wishlist/").status_code, 401)
        self.assertEqual(
            post_json(self.client, "/api/wishlist/", {"product": self.product.pk}).status_code,
            401,
        )
        self.assertEqual(
            self.client.delete(f"/api/wishlist/{self.product.pk}/").status_code, 401
        )

    def test_toggle_adds_then_removes(self):
        self.client.force_login(self.alice)

        response = post_json(self.client, "/api/wishlist/", {"product": self.product.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response), {"product_id": self.product.pk, "wishlisted": True})
        self.assertEqual(Wishlist.objects.filter(user=self.alice).count(), 1)

        response = post_json(self.client, "/api/wishlist/", {"product": self.product.pk})
        self.assertEqual(json_body(response)["wishlisted"], False)
        self.assertEqual(Wishlist.objects.filter(user=self.alice).count(), 0)

    def test_toggle_accepts_slug(self):
        self.client.force_login(self.alice)
        response = post_json(self.client, "/api/wishlist/", {"product": self.product.slug})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response)["wishlisted"], True)

    def test_list_and_delete(self):
        self.client.force_login(self.alice)
        post_json(self.client, "/api/wishlist/", {"product": self.product.pk})
        post_json(self.client, "/api/wishlist/", {"product": self.other.pk})

        data = json_body(self.client.get("/api/wishlist/"))
        self.assertEqual(data["meta"]["count"], 2)
        self.assertEqual(
            {row["slug"] for row in data["products"]},
            {self.product.slug, self.other.slug},
        )
        self.assertIn("price", data["products"][0])

        response = self.client.delete(f"/api/wishlist/{self.product.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_body(response), {"product_id": self.product.pk, "wishlisted": False})
        self.assertEqual(Wishlist.objects.count(), 1)

        self.assertEqual(
            self.client.delete(f"/api/wishlist/{self.product.pk}/").status_code, 404
        )
        self.assertEqual(self.client.delete("/api/wishlist/999999/").status_code, 404)

    def test_wishlist_is_per_user(self):
        self.client.force_login(self.alice)
        post_json(self.client, "/api/wishlist/", {"product": self.product.pk})
        bob = make_user("bob", "bobpw")
        self.client.force_login(bob)
        data = json_body(self.client.get("/api/wishlist/"))
        self.assertEqual(data["meta"]["count"], 0)

    def test_unknown_or_disabled_product_is_400(self):
        self.client.force_login(self.alice)
        response = post_json(self.client, "/api/wishlist/", {"product": 999999})
        self.assertEqual(response.status_code, 400)
        response = post_json(self.client, "/api/wishlist/", {})
        self.assertEqual(response.status_code, 400)
        retired = make_product("Retired", self.category, price="5.00", is_active=False)
        response = post_json(self.client, "/api/wishlist/", {"product": retired.pk})
        self.assertEqual(response.status_code, 400)


class AuthSessionTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("user", "userpw")

    def test_login_success_and_me(self):
        response = post_json(
            self.client, "/api/auth/login/",
            {"username": "user", "password": "userpw"},
        )
        self.assertEqual(response.status_code, 200)
        payload = json_body(response)["user"]
        self.assertEqual(payload["username"], "user")
        self.assertEqual(payload["role"], "client")
        self.assertFalse(payload["is_staff"])

        me = json_body(self.client.get("/api/auth/me/"))["user"]
        self.assertEqual(me["username"], "user")

    def test_login_bad_credentials_is_401(self):
        response = post_json(
            self.client, "/api/auth/login/",
            {"username": "user", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", json_body(response))

    def test_login_missing_fields_is_400(self):
        response = post_json(self.client, "/api/auth/login/", {"username": "user"})
        self.assertEqual(response.status_code, 400)
        errors = json_body(response)["errors"]
        self.assertIn("password", errors)

    def test_me_anonymous_is_401(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_anonymous_cart_is_adopted_on_login(self):
        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 2})
        self.assertEqual(Cart.objects.filter(user__isnull=True).count(), 1)

        response = post_json(
            self.client, "/api/auth/login/",
            {"username": "user", "password": "userpw"},
        )
        self.assertEqual(response.status_code, 200)

        cart = Cart.objects.get()
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
        data = json_body(self.client.get("/api/cart/"))["cart"]
        self.assertEqual(data["item_count"], 2)
        self.assertEqual(data["items"][0]["product"]["slug"], self.product.slug)

    def test_anonymous_cart_merges_into_an_existing_user_cart(self):
        user_cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=user_cart, product=self.product, quantity=1)

        post_json(self.client, "/api/cart/items/",
                  {"product": self.product.slug, "quantity": 2})
        post_json(
            self.client, "/api/auth/login/",
            {"username": "user", "password": "userpw"},
        )

        cart = Cart.objects.get()
        self.assertEqual(cart.pk, user_cart.pk)
        self.assertEqual(cart.item_count, 3)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_logout_clears_the_session(self):
        self.client.force_login(self.user)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_logout_anonymous_is_also_204(self):
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)


class NewsletterTests(ApiTestCase):
    def test_subscribe_new_email_is_201(self):
        response = post_json(self.client, "/api/newsletter/", {"email": "fan@plant.io"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json_body(response)["email"], "fan@plant.io")
        subscriber = Subscriber.objects.get()
        self.assertTrue(subscriber.is_active)

    def test_duplicate_subscribe_is_200(self):
        post_json(self.client, "/api/newsletter/", {"email": "fan@plant.io"})
        response = post_json(self.client, "/api/newsletter/", {"email": "FAN@plant.io"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("already", json_body(response)["detail"])
        self.assertEqual(Subscriber.objects.count(), 1)

    def test_unsubscribed_email_is_resubscribed(self):
        Subscriber.objects.create(email="gone@plant.io", is_active=False)
        response = post_json(self.client, "/api/newsletter/", {"email": "gone@plant.io"})
        self.assertEqual(response.status_code, 200)
        subscriber = Subscriber.objects.get(email="gone@plant.io")
        self.assertTrue(subscriber.is_active)

    def test_invalid_email_is_400(self):
        response = post_json(self.client, "/api/newsletter/", {"email": "not-an-email"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", json_body(response)["errors"])

        response = post_json(self.client, "/api/newsletter/", {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", json_body(response)["errors"])
