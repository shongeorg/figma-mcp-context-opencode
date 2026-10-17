from __future__ import annotations

import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from catalog import services
from catalog.models import (
    Category,
    Product,
    ProductImage,
    ProductSize,
    Review,
    Size,
    Tag,
)
from core.models import Address, Subscriber
from orders.models import Cart, CartItem, Order, OrderItem

User = get_user_model()

STATIC_IMAGES = Path(settings.BASE_DIR) / "static" / "images"
MEDIA_PRODUCTS = Path(settings.MEDIA_ROOT) / "products"


CATEGORY_TREE = [
    ("House Plants", 33, [("Foliage", 14), ("Flowering", 11), ("Palms", 8)]),
    ("Potter Plants", 12, [("Ceramic Pots", 7), ("Hanging Baskets", 5)]),
    ("Seeds", 65, [("Vegetable Seeds", 25), ("Flower Seeds", 24), ("Herb Seeds", 16)]),
    ("Small Plants", 39, [("Desk Plants", 22), ("Mini Pots", 17)]),
    ("Big Plants", 23, [("Floor Plants", 14), ("Outdoor Giants", 9)]),
    ("Succulents", 17, [("Cacti", 9), ("Echeveria", 8)]),
    ("Terrariums", 19, [("Closed Terrariums", 11), ("Open Terrariums", 8)]),
]


HERO_PRODUCTS = [
    {
        "name": "Barberton Daisy",
        "image": "plant-barberton-daisy.png",
        "category": "Flowering",
        "price": "119.00", "old_price": None,
        "tags": ["Flowering", "Red", "Home"],
        "short": "A cheerful daisy that flowers almost year round.",
        "description": (
            "The Barberton Daisy brings a burst of colour to any windowsill. "
            "Its ray florets open in the morning and close again at dusk, "
            "rewarding a bright spot with months of blooms."
        ),
        "featured": True, "is_new": False,
    },
    {
        "name": "Angel Wing Begonia",
        "image": "plant-angel-wing-begonia.png",
        "category": "Foliage",
        "price": "169.00", "old_price": None,
        "tags": ["Flowering", "Home", "Garden"],
        "short": "Winged leaves with silver spots and pendant flower sprays.",
        "description": (
            "A cane begonia prized for its asymmetrical, wing-shaped foliage. "
            "Kept in bright indirect light it rewards you with dangling clusters "
            "of coral flowers through the warmer months."
        ),
        "featured": True, "is_new": False,
    },
    {
        "name": "African Violet",
        "image": "plant-african-violet.png",
        "category": "Flowering",
        "price": "199.00", "old_price": "229.00",
        "tags": ["Flowering", "Home", "Plants"],
        "short": "Velvet leaves and a constant supply of purple blooms.",
        "description": (
            "One of the most rewarding house plants there is. With a little "
            "bottom watering and a bright north-facing sill, an African Violet "
            "flowers almost without a break."
        ),
        "featured": True, "is_new": False,
    },
    {
        "name": "Beach Spider Lily",
        "image": "plant-beach-spider-lily.png",
        "category": "Flowering",
        "price": "129.00", "old_price": None,
        "tags": ["Flowering", "Red", "Garden"],
        "short": "Strappy leaves topped with spidery white blooms.",
        "description": (
            "A coastal beauty that tolerates salt air and drought once "
            "established. Plant it in a group for a display that looks far "
            "hardier than it is."
        ),
        "featured": False, "is_new": False,
    },
    {
        "name": "Blushing Bromeliad",
        "image": "plant-blushing-bromeliad.png",
        "category": "Foliage",
        "price": "139.00", "old_price": None,
        "tags": ["Flowering", "Home"],
        "short": "A rosette that blushes pink as it comes into flower.",
        "description": (
            "Fill the central tank with water, not the compost, and this "
            "bromeliad will look after itself. The rosette colours up weeks "
            "before the actual flower spike appears."
        ),
        "featured": False, "is_new": False,
    },
    {
        "name": "Aluminum Plant",
        "image": "plant-aluminum-plant.png",
        "category": "Foliage",
        "price": "179.00", "old_price": None,
        "tags": ["Plants", "Home"],
        "short": "Silver-patched leaves on neat, compact stems.",
        "description": (
            "Named for the metallic sheen on its foliage, this is an "
            "undemanding plant that keeps a tidy shape. Pinch the tips in "
            "spring to keep it bushy."
        ),
        "featured": False, "is_new": False,
    },
    {
        "name": "Broadleaf Lady Palm",
        "image": "plant-broadleaf-lady-palm.png",
        "category": "Palms",
        "price": "189.00", "old_price": None,
        "tags": ["Garden", "Plants"],
        "short": "Fan-shaped fronds and a tolerance for low light.",
        "description": (
            "The most forgiving of the indoor palms. Give it a bright corner "
            "and it will grow into a proper statement plant without demanding "
            "much in return."
        ),
        "featured": True, "is_new": True,
    },
    {
        "name": "Bird's Nest Fern",
        "image": "plant-birds-nest-fern.png",
        "category": "Foliage",
        "price": "159.00", "old_price": None,
        "tags": ["Plants", "Home"],
        "short": "Glossy fronds unfurling from a central rosette.",
        "description": (
            "Unlike most ferns, the Bird's Nest Fern has undivided, glossy "
            "fronds that shed dust easily. It likes humidity, so a bathroom "
            "sill suits it perfectly."
        ),
        "featured": False, "is_new": True,
    },
    {
        "name": "Chinese Evergreen",
        "image": "plant-chinese-evergreen.png",
        "category": "Foliage",
        "price": "149.00", "old_price": "179.00",
        "tags": ["Plants", "Garden"],
        "short": "Marbled foliage that shrugs off neglect.",
        "description": (
            "A starter plant in the best sense: it tolerates low light, "
            "irregular watering and the odd cold draught, while its patterned "
            "leaves keep it interesting all year."
        ),
        "featured": False, "is_new": False,
    },
]


FILLER_NAMES = {
    "Foliage": [
        "Golden Pothos", "Marble Queen Pothos", "Philodendron Brasil",
        "Heartleaf Philodendron", "Monstera Deliciosa", "Swiss Cheese Vine",
        "ZZ Plant", "Snake Plant", "Rubber Plant", "Fiddle Leaf Fig",
        "Dumb Cane", "Dieffenbachia Camille", "Peace Lily", "Calathea Orbifolia",
        "Prayer Plant", "Polka Dot Plant", "Satin Pothos", "Alocasia Polly",
        "String of Hearts", "Tradescantia Zebrina", "Wandering Jew",
        "Spider Plant", "Parlour Palm", "Kentia Palm", "Areca Palm",
        "Boston Fern", "Maidenhair Fern", "Asparagus Fern", "Button Fern",
        "Norfolk Island Pine", "Schefflera Arboricola", "Croton Petra",
        "Majesty Palm", "Dracaena Janet Craig", "Money Tree", "Umbrella Tree",
        "Heartleaf Philodendron Silver", "Snow Queen Pothos", "Green Gem",
        "Variegated Umbrella",
    ],
    "Flowering": [
        "Anthurium Red", "Phalaenopsis Orchid", "Moth Orchid White",
        "Peace Lily Bloom", "Begonia Maculata", "Hoya Carnosa",
        "Jasmine Polyanthum", "Gloxinia", "Kalanchoe Calandiva",
        "Cyclamen Persicum", "Primrose Indica", "Clivia Miniata",
        "Amaryllis Red Lion", "Bromelia Nuptialis", "Ixora Coccinea",
        "Mandevilla Sundaville", "Passion Flower", "Hibiscus Rosa",
        "Camellia japonica", "Gardenia Fortunei", "Stephanotis Floribunda",
        "Plumeria Frangipani", "Tibouchina", "Crossandra Infundibuliformis",
    ],
    "Palms": [
        "Rhopalis Palma", "Fishtail Palm", "Lady Palm Rhapis",
        "Pygmy Date Palm", "Chamaedorea Elegans", "Licuala Grandis",
        "Bismarck Palm", "Travelers Palm", "Coconut Palm Dwarf",
        "Foxtail Palm", "Alexander Palm", "Bucida Buceras",
        "Sago Palm", "Cycas Revoluta", "Windmill Palm",
        "Majesty Palm XL", "Hawaiian Palm", "Dypsis Lutescens",
    ],
    "Ceramic Pots": [
        "Terracotta Planter Round", "Glazed Pot Forest Green",
        "Matte Ceramic Pot White", "Speckled Stoneware Pot",
        "Ribbed Ceramic Planter", "Hand-thrown Clay Pot",
        "Concrete Look Planter",
    ],
    "Hanging Baskets": [
        "Macrame Plant Hanger", "Ceramic Hanging Planter", "Jute Basket Set",
        "Brass Chain Hanger", "Woven Seagrass Basket",
    ],
    "Vegetable Seeds": [
        "Tomato Seeds", "Cucumber Seeds", "Sweet Pepper Seeds",
        "Aubergine Seeds", "Courgette Seeds", "Carrot Seeds Nantes",
        "Beetroot Seeds", "Radish Seeds", "Lettuce Seeds Mixed",
        "Spinach Seeds", "Kale Seeds", "Broccoli Seeds",
        "Cauliflower Seeds", "Cabbage Seeds", "Leek Seeds",
        "Onion Seeds", "Garlic Bulbs", "Celery Seeds",
        "Pumpkin Seeds", "Melon Seeds", "Sweetcorn Seeds",
        "Bean Seeds Runner", "Pea Seeds", "Chilli Seeds Hot",
        "Potato Seed",
    ],
    "Flower Seeds": [
        "Sunflower Seeds", "Poppy Seeds Mixed", "Marigold Seeds",
        "Nasturtium Seeds", "Cosmos Seeds", "Zinnia Seeds",
        "Aster Seeds", "Dahlia Seeds", "Petunia Seeds",
        "Lavender Seeds", "Snapdragon Seeds", "Cornflower Seeds",
        "Sweet Pea Seeds", "Primula Seeds", "Pansy Seeds",
        "Begonia Seeds", "Geranium Seeds", "Impatiens Seeds",
        "Lobelia Seeds", "Verbena Seeds", "Calendula Seeds",
        "Dianthus Seeds", "Gazania Seeds", "Verbena Bonariensis",
    ],
    "Herb Seeds": [
        "Basil Seeds", "Parsley Seeds", "Dill Seeds",
        "Coriander Seeds", "Mint Seeds", "Oregano Seeds",
        "Thyme Seeds", "Rosemary Seeds", "Sage Seeds",
        "Chives Seeds", "Bay Leaf Seeds", "Tarragon Seeds",
        "Lemongrass Seeds", "Cumin Seeds", "Fennel Seeds",
        "Chamomile Seeds",
    ],
    "Desk Plants": [
        "Mini Bonsai Juniper", "Succulent Assortment", "Air Plant Trio",
        "Cactus Trio", "Bonsai Ficus", "Lucky Bamboo",
        "Aloe Vera Mini", "Haworthia Zebra", "Peperomia Obtusifolia",
        "String of Pearls", "Burro's Tail", "Jade Plant Mini",
        "Oxalis Triangularis", "Fittonia Pink", "Fittonia White",
        "Pilea Peperomioides", "Baby Rubber Plant", "Friendship Plant",
        "Baby Tears", "Selaginella", "Nerve Plant Mini",
        "Tiny Tim Tomato",
    ],
    "Mini Pots": [
        "Ceramic Egg Cup Pot", "Tiny Terracotta Set", "Mini Glazed Pot Trio",
        "Concrete Cube Planter", "Pastel Ceramic Pot", "Stone Look Mini Pot",
        "Hand-painted Mini Pot", "Bamboo Pot Small", "Recycled Glass Pot",
        "Two-tone Ceramic Pot", "Slipware Pot", "Milk Jug Planter",
        "Hexagon Planter", "Bud Vase Planter", "Chalk White Pot",
        "Charcoal Mini Pot", "Sand Dune Pot",
    ],
    "Floor Plants": [
        "Giant Monstera", "Fiddle Leaf Fig XL", "Bird of Paradise",
        "Rubber Tree Burgundy", "Weeping Fig", "Dragon Tree",
        "Yucca Elephantipes", "Dracaena Marginata", "Corn Plant",
        "Philodendron Xanadu", "Kentia Palm Floor", "Areca Palm Tall",
        "Ficus Lyrata Bambino", "Bamboo Palm",
    ],
    "Outdoor Giants": [
        "Olive Tree Potted", "Lemon Tree Potted", "Fig Tree Brown Turkey",
        "Bay Tree Standard", "Magnolia Grandiflora", "Camellia Sasanqua",
        "Pittosporum Tobira", "Viburnum Tinus", "Photinia Red Robin",
    ],
    "Cacti": [
        "Golden Barrel Cactus", "Old Man Cactus", "Fairy Castle Cactus",
        "Bunny Ear Cactus", "Christmas Cactus", "Echinopsis Lobivia",
        "Mammillaria Mix", "Rat Tail Cactus", "Clump Cactus Trio",
    ],
    "Echeveria": [
        "Echeveria Lola", "Echeveria Perle Von Nurnberg", "Echeveria Black Prince",
        "Echeveria Lilacina", "Echeveria Blue Bird", "Echeveria Agavoides",
        "Sedum Rubrotinctum", "Crassula Ovata",
    ],
    "Closed Terrariums": [
        "Moss Terrarium Sphere", "Fern Terrarium Jar", "Succulent Terrarium Bowl",
        "Tropical Terrarium Dome", "Closed Jar Garden", "Mini Jungle Terrarium",
        "Crystal Bowl Terrarium", "Hanging Glass Terrarium", "Layered Sand Terrarium",
        "Desert Closed Terrarium", "Woodland Terrarium",
    ],
    "Open Terrariums": [
        "Open Dish Garden", "Sand and Cactus Dish", "Open Fern Bowl",
        "Zen Pebble Garden", "Air Plant Dish", "Succulent Tray Garden",
        "Stone Open Terrarium", "Grass and Moss Dish",
    ],
}

TAGS = ["Flowering", "Red", "Yellow", "Home", "Garden", "Plants"]
SIZES = [("S", 1), ("M", 2), ("L", 3), ("XL", 4)]
SIZE_DELTA = {"S": Decimal("0.00"), "M": Decimal("6.00"),
              "L": Decimal("14.00"), "XL": Decimal("26.00")}

PRICE_BASE = {
    "Vegetable Seeds": Decimal("6.90"), "Flower Seeds": Decimal("5.90"),
    "Herb Seeds": Decimal("4.90"), "Ceramic Pots": Decimal("24.00"),
    "Hanging Baskets": Decimal("32.00"), "Cacti": Decimal("18.00"),
    "Echeveria": Decimal("16.00"), "Closed Terrariums": Decimal("54.00"),
    "Open Terrariums": Decimal("46.00"), "Mini Pots": Decimal("12.00"),
    "Desk Plants": Decimal("22.00"), "Floor Plants": Decimal("89.00"),
    "Outdoor Giants": Decimal("129.00"), "Foliage": Decimal("42.00"),
    "Flowering": Decimal("48.00"), "Palms": Decimal("79.00"),
}

TAGS_BY_SUBCATEGORY = {
    "Flowering": ["Flowering", "Home"],
    "Palms": ["Garden", "Plants"],
    "Foliage": ["Plants", "Home"],
    "Ceramic Pots": ["Home"],
    "Hanging Baskets": ["Home", "Garden"],
    "Vegetable Seeds": ["Garden"],
    "Flower Seeds": ["Flowering", "Garden"],
    "Herb Seeds": ["Garden", "Home"],
    "Desk Plants": ["Home", "Plants"],
    "Mini Pots": ["Home"],
    "Floor Plants": ["Plants", "Garden"],
    "Outdoor Giants": ["Garden"],
    "Cacti": ["Plants", "Home"],
    "Echeveria": ["Plants", "Home"],
    "Closed Terrariums": ["Home"],
    "Open Terrariums": ["Home", "Garden"],
}


class Command(BaseCommand):
    help = "Seed the demo catalogue to match the GreenShop mockup."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe", action="store_true",
            help="Delete existing catalogue and order data first.",
        )
        parser.add_argument(
            "--no-users", action="store_true",
            help="Skip creating the admin/client accounts.",
        )


    @transaction.atomic
    def handle(self, *args, **options):
        if options["wipe"]:
            self.wipe()

        self.size_by_name = self.seed_sizes()
        self.tag_by_name = self.seed_tags()
        self.category_by_name = self.seed_categories()
        self.seed_products()

        if not options["no_users"]:
            self.seed_users()

        self.seed_reviews()

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeded {Product.objects.count()} products, "
            f"{Category.objects.count()} categories, "
            f"{ProductImage.objects.count()} images, "
            f"{Review.objects.count()} reviews."
        ))
        self.stdout.write(self.style.SUCCESS(
            "Admin: admin / admin    Client: user / user"
        ))


    def wipe(self):
        self.stdout.write("Wiping catalogue and order data…")
        Order.objects.all().delete()
        Cart.objects.all().delete()
        Review.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()
        Size.objects.all().delete()
        Address.objects.all().delete()
        Subscriber.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(username="admin").delete()
        shutil.rmtree(MEDIA_PRODUCTS, ignore_errors=True)
        self.stdout.write(self.style.WARNING("  wiped."))


    def seed_sizes(self) -> dict:
        objects = [
            Size(name=name, ordering=order, slug=slugify(name).lower())
            for name, order in SIZES
        ]
        Size.objects.bulk_create(objects, ignore_conflicts=True)
        self.stdout.write(f"  {len(objects)} sizes: "
                          f"{', '.join(n for n, _ in SIZES)}")
        return {s.name: s for s in Size.objects.all()}

    def seed_tags(self) -> dict:
        Tag.objects.bulk_create(
            [Tag(name=name, slug=slugify(name).lower()) for name in TAGS],
            ignore_conflicts=True,
        )
        self.stdout.write(f"  {len(TAGS)} tags")
        return {t.name: t for t in Tag.objects.all()}

    def seed_categories(self) -> dict:
        to_create: list[Category] = []
        parent_ids: dict[str, int | None] = {}

        for order, (name, _total, children) in enumerate(CATEGORY_TREE, start=1):
            to_create.append(Category(
                name=name, slug=slugify(name).lower(),
                ordering=order, is_active=True,
            ))
            for child_order, (child_name, _count) in enumerate(children, start=1):
                to_create.append(Category(
                    name=child_name, slug=slugify(child_name).lower(),
                    ordering=child_order, is_active=True,
                ))

        Category.objects.bulk_create(to_create, ignore_conflicts=True)
        existing = {c.name: c for c in Category.objects.all()}

        updates = []
        for name, _total, children in CATEGORY_TREE:
            parent = existing[name]
            parent.parent = None
            updates.append(parent)
            for child_order, (child_name, _count) in enumerate(children, start=1):
                child = existing[child_name]
                child.parent = parent
                child.ordering = child_order
                updates.append(child)
        Category.objects.bulk_update(updates, ["parent", "ordering", "updated_at"])

        self.stdout.write(f"  {len(existing)} categories "
                          f"({len(CATEGORY_TREE)} roots + "
                          f"{sum(len(c[2]) for c in CATEGORY_TREE)} subcategories)")
        return existing


    def seed_products(self):
        MEDIA_PRODUCTS.mkdir(parents=True, exist_ok=True)
        photo_paths: dict[str, str] = {}
        for spec in HERO_PRODUCTS:
            source = STATIC_IMAGES / spec["image"]
            if not source.exists():
                continue
            destination = MEDIA_PRODUCTS / spec["image"]
            shutil.copy2(source, destination)
            photo_paths[spec["image"]] = f"products/{destination.name}"

        rows: list[dict] = []
        used_slugs: set[str] = set()
        used_names: set[str] = set()

        def next_row(name, category, price, old_price, short, description,
                     tag_names, ordering, featured, is_new, stock, photo):
            slug = slugify(name).lower()
            base, counter = slug, 2
            while slug in used_slugs:
                slug = f"{base}-{counter}"
                counter += 1
            used_slugs.add(slug)
            used_names.add(name)
            rows.append({
                "name": name, "slug": slug,
                "sku": f"GS{len(rows) + 1:04d}",
                "category": category,
                "price": Decimal(price),
                "old_price": Decimal(old_price) if old_price else None,
                "short_description": short, "description": description,
                "tag_names": tag_names, "ordering": ordering,
                "is_featured": featured, "is_new": is_new,
                "is_active": True, "stock": stock, "photo": photo,
            })

        for index, spec in enumerate(HERO_PRODUCTS):
            next_row(
                name=spec["name"],
                category=self.category_by_name[spec["category"]],
                price=spec["price"], old_price=spec["old_price"],
                short=spec["short"], description=spec["description"],
                tag_names=spec["tags"], ordering=index,
                featured=spec["featured"], is_new=spec["is_new"],
                stock=25, photo=photo_paths.get(spec["image"]),
            )

        hero_counts: dict[str, int] = {}
        for spec in HERO_PRODUCTS:
            hero_counts[spec["category"]] = hero_counts.get(spec["category"], 0) + 1

        counter = len(HERO_PRODUCTS)
        for name, _total, children in CATEGORY_TREE:
            for child_name, target in children:
                already = hero_counts.get(child_name, 0)
                pool = FILLER_NAMES.get(child_name, [])
                need = max(target - already, 0)
                base_price = PRICE_BASE.get(child_name, Decimal("29.00"))
                for i in range(need):
                    if pool:
                        base = pool[i % len(pool)]
                        repeat = i // len(pool) + 2
                    else:
                        base = f"{child_name} #{i + 1}"
                        repeat = 1
                    product_name = base if base not in used_names else f"{base} {repeat}"

                    price = base_price + Decimal(i % 9) * Decimal("3.50")
                    old_price = f"{price * Decimal('1.15'):.2f}" if i % 4 == 3 else None

                    photo_keys = list(photo_paths)
                    photo = photo_keys[counter % len(photo_keys)] if photo_keys else None

                    next_row(
                        name=product_name,
                        category=self.category_by_name[child_name],
                        price=f"{price:.2f}", old_price=old_price,
                        short=f"{product_name} — a {child_name.lower()} pick from our nursery.",
                        description=(
                            f"The {product_name} is grown on in our own greenhouse and "
                            f"supplied in a 12 cm pot. It belongs to the {child_name} "
                            f"collection and ships well rooted."
                        ),
                        tag_names=TAGS_BY_SUBCATEGORY.get(child_name, ["Plants"]),
                        ordering=counter,
                        featured=(counter % 11 == 0),
                        is_new=(counter % 9 == 0),
                        stock=8 + (counter % 17),
                        photo=photo_paths.get(photo) if photo else None,
                    )
                    counter += 1

        products = Product.objects.bulk_create(
            [Product(
                name=r["name"], slug=r["slug"], sku=r["sku"],
                category=r["category"], price=r["price"], old_price=r["old_price"],
                short_description=r["short_description"], description=r["description"],
                ordering=r["ordering"], is_featured=r["is_featured"],
                is_new=r["is_new"], is_active=True, stock=r["stock"],
            ) for r in rows],
            batch_size=100,
        )

        through = Product.tags.through
        through_rows = []
        tag_by_name = self.tag_by_name
        for row, product in zip(rows, products):
            for tag_name in row["tag_names"]:
                tag = tag_by_name.get(tag_name)
                if tag is not None:
                    through_rows.append(through(product_id=product.pk, tag_id=tag.pk))
        through.objects.bulk_create(through_rows, ignore_conflicts=True, batch_size=500)

        size_rows = []
        size_order = [n for n, _ in SIZES]
        for row, product in zip(rows, products):
            for position, size_name in enumerate(size_order):
                size = self.size_by_name.get(size_name)
                if size is None:
                    continue
                size_rows.append(ProductSize(
                    product_id=product.pk, size_id=size.pk,
                    price_delta=SIZE_DELTA[size_name],
                    stock=max(row["stock"] - position * 2, 0),
                    is_active=True,
                ))
        ProductSize.objects.bulk_create(size_rows, ignore_conflicts=True, batch_size=500)

        image_rows = []
        for row, product in zip(rows, products):
            if not row["photo"]:
                continue
            image_rows.append(ProductImage(
                product_id=product.pk, image=row["photo"],
                alt=product.name, is_primary=True, ordering=0,
            ))
        ProductImage.objects.bulk_create(image_rows, batch_size=500)

        self.stdout.write(f"  {len(products)} products, "
                          f"{len(size_rows)} size rows, {len(image_rows)} images")


    def seed_users(self):
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@greenshop.local",
                "first_name": "Green",
                "last_name": "Shop",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin")
            admin.save(update_fields=["password"])
            self.stdout.write("  created user admin / admin")

        client, created = User.objects.get_or_create(
            username="user",
            defaults={
                "email": "user@greenshop.local",
                "first_name": "Valentyn",
                "last_name": "Shovkoplias",
                "role": User.Role.CLIENT,
                "phone": "+380 63 123 45 67",
            },
        )
        if created:
            client.set_password("user")
            client.save(update_fields=["password"])
            self.stdout.write("  created user user / user")

        Address.objects.get_or_create(
            user=client,
            label=Address.Label.HOME,
            defaults={
                "full_name": client.get_full_name(),
                "phone": client.phone,
                "line1": "17 Green Street",
                "city": "Kyiv",
                "region": "Kyiv Region",
                "postal_code": "01001",
                "country": "Ukraine",
                "is_default": True,
            },
        )
        Subscriber.objects.get_or_create(email="user@greenshop.local")
        self.seed_sample_order(client)

    def seed_sample_order(self, client):
        if Order.objects.exists():
            return

        hero = list(Product.objects.filter(
            name__in=[p["name"] for p in HERO_PRODUCTS]
        ).order_by("ordering")[:3])
        if not hero:
            return

        order_items = []
        for status, paid, picks in (
            (Order.Status.DELIVERED, True, hero[:2]),
            (Order.Status.NEW, False, hero[:3]),
        ):
            subtotal = Decimal("0.00")
            order = Order.objects.create(
                user=client,
                full_name=client.get_full_name(),
                email=client.email,
                phone=client.phone,
                address_line="17 Green Street",
                city="Kyiv",
                region="Kyiv Region",
                postal_code="01001",
                country="Ukraine",
                status=status,
                payment_method=Order.PaymentMethod.COD,
                is_paid=paid,
            )
            for product in picks:
                line_total = product.price * 2
                order_items.append(OrderItem(
                    order=order, product=product,
                    product_name=product.name, product_slug=product.slug,
                    sku=product.sku, image_url=product.image_url,
                    quantity=2, unit_price=product.price, line_total=line_total,
                ))
                subtotal += line_total

            shipping = Decimal("0.00") if subtotal >= Decimal("120.00") else Decimal("9.00")
            order.subtotal = subtotal
            order.shipping = shipping
            order.total = subtotal + shipping
            order.save(update_fields=["subtotal", "shipping", "total", "updated_at"])

        OrderItem.objects.bulk_create(order_items)
        self.stdout.write("  2 sample orders")


    def seed_reviews(self):
        if Review.objects.exists():
            return

        samples = [
            ("Barberton Daisy", 5, "Arrived in perfect condition",
             "Packaging was careful and the plant had three open flowers already."),
            ("Barberton Daisy", 4, "Lovely colour",
             "Slightly smaller than expected but healthy and flowering."),
            ("African Violet", 5, "Worth the discount",
             "Bought it on sale and it has not stopped blooming since."),
            ("African Violet", 5, "Second one I have bought",
             "Ordered a second for my sister. Consistent quality."),
            ("Angel Wing Begonia", 4, "Great foliage",
             "The silver spotting is even nicer in person."),
            ("Broadleaf Lady Palm", 5, "Tolerates my dark hallway",
             "Six months in and it is still pushing out new fronds."),
            ("Aluminum Plant", 3, "Healthy but droopy on arrival",
             "It recovered within a week. Fine after that."),
        ]

        products = {p.name: p for p in Product.objects.filter(
            name__in=[s[0] for s in samples]
        )}
        if not products:
            return

        reviewers = []
        for index in range(len(samples)):
            user, _ = User.objects.get_or_create(
                email=f"reviewer{index}@example.com",
                defaults={
                    "username": f"reviewer_{index}",
                    "first_name": samples[index][2].split()[0],
                    "last_name": "K.",
                },
            )
            if not user.has_usable_password():
                user.set_password("demo")
                user.save(update_fields=["password"])
            reviewers.append(user)

        reviews = []
        for index, (name, rating, title, body) in enumerate(samples):
            product = products.get(name)
            if product is None:
                continue
            reviews.append(Review(
                product=product, user=reviewers[index],
                rating=rating, title=title, body=body, is_approved=True,
            ))
        Review.objects.bulk_create(reviews)

        now = timezone.now()
        for index, review in enumerate(reviews):
            Review.objects.filter(pk=review.pk).update(
                created_at=now - timezone.timedelta(days=index * 4 + 2)
            )

        client = User.objects.filter(username="user").first()
        pending_product = Product.objects.filter(name="Beach Spider Lily").first()
        if client is not None and pending_product is not None:
            Review.objects.get_or_create(
                product=pending_product, user=client,
                defaults={
                    "rating": 4,
                    "title": "Waiting to be published",
                    "body": "Submitted from the storefront — this one is still pending approval.",
                    "is_approved": False,
                },
            )

        for product in Product.objects.all():
            services.refresh_product_rating(product.pk)

        approved = Review.objects.filter(is_approved=True).count()
        self.stdout.write(f"  {approved} approved reviews (+1 pending)")
