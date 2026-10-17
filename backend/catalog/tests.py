from __future__ import annotations

from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase

from . import services
from .models import Category, Product, ProductImage, ProductSize, Size, Tag


def make_category(name: str, parent: Category | None = None, **kwargs) -> Category:
    return Category.objects.create(name=name, parent=parent, **kwargs)


def make_product(category: Category | None = None, name: str = "Fiddle Leaf Fig", **kwargs) -> Product:
    if category is None:
        category, _ = Category.objects.get_or_create(name="Default Category", defaults={})
    defaults = {"category": category, "price": Decimal("19.99"), "stock": 10}
    defaults.update(kwargs)
    return Product.objects.create(name=name, **defaults)


def make_size(name: str, ordering: int = 0) -> Size:
    return Size.objects.create(name=name, ordering=ordering)


def make_product_size(product: Product, size: Size, **kwargs) -> ProductSize:
    defaults = {"stock": 5}
    defaults.update(kwargs)
    return ProductSize.objects.create(product=product, size=size, **kwargs)


def make_image(product: Product, **kwargs) -> ProductImage:
    defaults = {"image": "products/test.jpg"}
    defaults.update(kwargs)
    return ProductImage.objects.create(product=product, **defaults)


def make_tag(name: str, **kwargs) -> Tag:
    return Tag.objects.create(name=name, **kwargs)


class ProductPrimaryImageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.multi = make_product(name="Multi Shot Fern")
        make_image(self.multi, image="products/a.jpg", ordering=1)
        make_image(self.multi, image="products/b.jpg", ordering=2, is_primary=True)

        self.fallback = make_product(name="Fallback Pothos")
        make_image(self.fallback, image="products/c.jpg", ordering=5)
        make_image(self.fallback, image="products/d.jpg", ordering=9)

        self.bare = make_product(name="Bare Cactus")

    def test_prefetched_access_issues_zero_queries(self):
        products = list(Product.objects.order_by("pk").prefetch_related("images"))
        self.assertEqual(len(products), 3)
        with self.assertNumQueries(0):
            images = [p.primary_image for p in products]
        self.assertEqual(
            [img.image.name if img else None for img in images],
            ["products/b.jpg", "products/c.jpg", None],
        )

    def test_repeated_access_is_memoised(self):
        product = Product.objects.get(pk=self.multi.pk)
        self.assertIsNotNone(product.primary_image)
        with self.assertNumQueries(0):
            self.assertEqual(product.primary_image.image.name, "products/b.jpg")

    def test_is_primary_flag_wins(self):
        product = Product.objects.prefetch_related("images").get(pk=self.multi.pk)
        image = product.primary_image
        self.assertTrue(image.is_primary)
        self.assertEqual(image.image.name, "products/b.jpg")

    def test_falls_back_to_first_image_when_none_marked_primary(self):
        product = Product.objects.prefetch_related("images").get(pk=self.fallback.pk)
        self.assertEqual(product.primary_image.image.name, "products/c.jpg")

    def test_returns_none_without_images(self):
        product = Product.objects.prefetch_related("images").get(pk=self.bare.pk)
        self.assertIsNone(product.primary_image)

    def test_image_url_empty_without_images(self):
        self.assertEqual(self.bare.image_url, "")

    def test_image_url_is_the_field_url(self):
        product = Product.objects.prefetch_related("images").get(pk=self.multi.pk)
        self.assertEqual(product.image_url, product.primary_image.image.url)


class ProductGetSizesTests(TestCase):
    def setUp(self):
        cache.clear()
        self.product = make_product(name="Sized Fern")
        self.small = make_size("Small")
        self.large = make_size("Large", ordering=1)
        self.small_row = make_product_size(self.product, self.small, is_active=True)
        self.large_row = make_product_size(self.product, self.large, is_active=False)

    def test_prefetched_sizes_cost_zero_queries_and_filter_inactive(self):
        product = Product.objects.prefetch_related("sizes__size").get(pk=self.product.pk)
        with self.assertNumQueries(0):
            rows = list(product.get_sizes())
        self.assertEqual([row.pk for row in rows], [self.small_row.pk])
        with self.assertNumQueries(0):
            self.assertEqual([row.size.name for row in rows], ["Small"])

    def test_without_prefetch_returns_filtered_queryset(self):
        product = Product.objects.get(pk=self.product.pk)
        rows = list(product.get_sizes())
        self.assertEqual([row.pk for row in rows], [self.small_row.pk])

    def test_fallback_queryset_selects_the_size_row(self):
        product = Product.objects.get(pk=self.product.pk)
        with self.assertNumQueries(1):
            rows = list(product.get_sizes())
        with self.assertNumQueries(0):
            self.assertEqual([row.size.name for row in rows], ["Small"])


class CategoryFamilyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = make_category("House Plants")
        self.child = make_category("Indoor Plants", parent=self.root)
        self.leaf = make_category("Hanging Plants", parent=self.child)
        self.other = make_category("Succulents")

    def test_family_ids_includes_self_and_all_descendants(self):
        ids = self.root.get_family_ids()
        self.assertCountEqual(ids, [self.root.pk, self.child.pk, self.leaf.pk])

    def test_family_ids_for_child_excludes_ancestors(self):
        ids = self.child.get_family_ids()
        self.assertCountEqual(ids, [self.child.pk, self.leaf.pk])

    def test_cold_call_runs_one_query_then_hits_the_cache(self):
        cache.clear()
        with self.assertNumQueries(1):
            self.root.get_family_ids()
        with self.assertNumQueries(0):
            self.assertCountEqual(
                self.root.get_family_ids(), [self.root.pk, self.child.pk, self.leaf.pk]
            )

    def test_category_created_after_the_cache_is_warm_only_knows_itself(self):
        self.root.get_family_ids()
        newborn = make_category("New Category")
        self.assertEqual(newborn.get_family_ids(), [newborn.pk])

    def test_descendants_exclude_self(self):
        ids = self.root.get_descendants_ids()
        self.assertNotIn(self.root.pk, ids)
        self.assertCountEqual(ids, [self.child.pk, self.leaf.pk])


class ProductQuerySetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = make_category("House Plants")
        self.child = make_category("Indoor Plants", parent=self.root)
        self.leaf = make_category("Hanging Plants", parent=self.child)
        self.unrelated = make_category("Garden Tools")

        self.in_root = make_product(self.root, name="Root Fern")
        self.in_child = make_product(self.child, name="Child Pothos")
        self.in_leaf = make_product(self.leaf, name="Leaf Ivy")
        self.outsider = make_product(self.unrelated, name="Steel Trowel")

    def test_in_category_includes_nested_subcategories(self):
        found = Product.objects.active().in_category(self.root)
        self.assertCountEqual(
            found.values_list("pk", flat=True),
            [self.in_root.pk, self.in_child.pk, self.in_leaf.pk],
        )

    def test_in_category_from_a_mid_level_node(self):
        found = Product.objects.active().in_category(self.child)
        self.assertCountEqual(
            found.values_list("pk", flat=True), [self.in_child.pk, self.in_leaf.pk]
        )

    def test_in_category_excludes_unrelated(self):
        found = Product.objects.active().in_category(self.root)
        self.assertNotIn(self.outsider.pk, found.values_list("pk", flat=True))

    def test_in_category_none_returns_everything(self):
        self.assertEqual(Product.objects.in_category(None).count(), 4)

    def test_active_filters_inactive_products(self):
        make_product(self.root, name="Retired Fern", is_active=False)
        self.assertEqual(Product.objects.active().count(), 4)
        self.assertEqual(Product.objects.count(), 5)

    def test_featured_requires_flag_and_active(self):
        make_product(self.root, name="Featured One", is_featured=True)
        make_product(self.root, name="Featured But Gone", is_featured=True, is_active=False)
        found = Product.objects.featured()
        self.assertEqual([p.name for p in found], ["Featured One"])

    def test_on_sale_requires_old_price_above_price_and_active(self):
        make_product(self.root, name="On Sale", price=Decimal("10.00"), old_price=Decimal("20.00"))
        make_product(self.root, name="Sale But Gone", price=Decimal("10.00"),
                     old_price=Decimal("20.00"), is_active=False)
        found = Product.objects.on_sale()
        self.assertEqual([p.name for p in found], ["On Sale"])


class SaleMathTests(TestCase):
    def test_is_on_sale_and_discount_percent(self):
        product = make_product(price=Decimal("199.00"), old_price=Decimal("229.00"))
        self.assertTrue(product.is_on_sale)
        self.assertEqual(product.discount_percent, 13)

    def test_discount_percent_rounds_half(self):
        product = make_product(price=Decimal("50.00"), old_price=Decimal("100.00"))
        self.assertEqual(product.discount_percent, 50)

    def test_no_old_price_is_not_a_sale(self):
        product = make_product(price=Decimal("19.99"))
        self.assertFalse(product.is_on_sale)
        self.assertIsNone(product.discount_percent)

    def test_save_drops_an_old_price_not_above_the_price(self):
        product = make_product(price=Decimal("20.00"), old_price=Decimal("18.00"))
        product.refresh_from_db()
        self.assertIsNone(product.old_price)
        self.assertFalse(product.is_on_sale)


class SidebarCountsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = make_category("House Plants")
        self.child = make_category("Indoor Plants", parent=self.root)
        self.leaf = make_category("Hanging Plants", parent=self.child)
        make_category("Succulents")
        make_category("Archived", is_active=False)

        tools = make_category("Garden Tools")

        self.p1 = make_product(self.root, name="Root Fern")
        self.p2 = make_product(self.child, name="Child Pothos")
        self.p3 = make_product(self.leaf, name="Leaf Ivy")
        make_product(self.child, name="Retired Pothos", is_active=False)
        make_product(tools, name="Steel Trowel")

        self.small = make_size("Small")
        medium = make_size("Medium", ordering=1)
        make_size("Large", ordering=2)
        make_product_size(self.p1, self.small)
        make_product_size(self.p2, self.small)
        make_product_size(Product.objects.get(name="Retired Pothos"), medium)

        cache.clear()

    def test_counts_cover_the_whole_subtree_per_root(self):
        counts = services.sidebar_counts()
        self.assertEqual(
            counts["categories"],
            {
                self.root.pk: 3,
                self.child.pk: 2,
                self.leaf.pk: 1,
                Category.objects.get(name="Garden Tools").pk: 1,
            },
        )

    def test_inactive_products_and_sizes_are_excluded(self):
        counts = services.sidebar_counts()
        self.assertNotIn(Category.objects.get(name="Archived").pk, counts["categories"])
        self.assertNotIn(Category.objects.get(name="Succulents").pk, counts["categories"])
        self.assertEqual(counts["sizes"], {self.small.pk: 2})

    def test_counts_are_cached_on_the_second_call(self):
        services.sidebar_counts()
        with self.assertNumQueries(0):
            counts = services.sidebar_counts()
        self.assertEqual(counts["categories"][self.root.pk], 3)

    def test_new_product_is_counted_immediately(self):
        services.sidebar_counts()
        make_product(self.leaf, name="New Fern")
        with self.assertNumQueries(2):
            counts = services.sidebar_counts()
        self.assertEqual(counts["categories"][self.root.pk], 4)
        self.assertEqual(counts["categories"][self.leaf.pk], 2)

    def test_saving_a_category_invalidates_the_cached_counts(self):
        services.sidebar_counts()
        with self.assertNumQueries(0):
            services.sidebar_counts()
        self.root.save()
        with self.assertNumQueries(2):
            services.sidebar_counts()


class CatalogCacheServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.root = make_category("House Plants")
        self.child = make_category("Indoor Plants", parent=self.root)
        make_category("Archived", is_active=False)
        self.small = make_size("Small")
        make_size("Large", ordering=1)
        make_tag("Care Tips")
        make_tag("Hidden", is_active=False)
        cache.clear()

    def test_nav_categories_cached_returns_active_roots_with_children(self):
        with self.assertNumQueries(2):
            first = services.nav_categories_cached()
        self.assertEqual([c.pk for c in first], [self.root.pk])
        with self.assertNumQueries(0):
            self.assertEqual([c.pk for c in first[0].children.all()], [self.child.pk])

        with self.assertNumQueries(0):
            second = services.nav_categories_cached()
        self.assertEqual([c.pk for c in second], [self.root.pk])

    def test_sizes_cached_returns_menu_order_then_cache(self):
        with self.assertNumQueries(1):
            first = services.sizes_cached()
        self.assertEqual([s.name for s in first], ["Small", "Large"])
        with self.assertNumQueries(0):
            second = services.sizes_cached()
        self.assertEqual([s.pk for s in second], [s.pk for s in first])

    def test_tags_cached_returns_only_active_rows_then_cache(self):
        with self.assertNumQueries(1):
            first = services.tags_cached()
        self.assertEqual([t.name for t in first], ["Care Tips"])
        with self.assertNumQueries(0):
            self.assertEqual([t.name for t in services.tags_cached()], ["Care Tips"])

    def test_family_ids_cache_and_invalidate_catalog_cache(self):
        cache.clear()
        with self.assertNumQueries(1):
            services.family_ids(self.root)
        with self.assertNumQueries(0):
            self.assertCountEqual(
                services.family_ids(self.root), [self.root.pk, self.child.pk]
            )
        services.invalidate_catalog_cache()
        with self.assertNumQueries(1):
            services.family_ids(self.root)

    def test_invalidate_catalog_cache_clears_the_sidebar_too(self):
        services.sidebar_counts()
        services.invalidate_catalog_cache()
        with self.assertNumQueries(2):
            services.sidebar_counts()
