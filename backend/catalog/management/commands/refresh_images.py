from __future__ import annotations

import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from catalog.models import Product, ProductImage

UNSPLASH_SEARCH = "https://api.unsplash.com/search/photos"
PEXELS_SEARCH = "https://api.pexels.com/v1/search"
PIXABAY_SEARCH = "https://pixabay.com/api/"

MAX_SOURCE_EDGE = 1400
JPEG_QUALITY = 85
REQUEST_TIMEOUT = 25
INTER_CALL_DELAY = 0.7
MAX_ATTEMPTS_PER_PRODUCT = 4

PROVIDER_ORDER = ("pixabay", "pexels", "unsplash")


class Command(BaseCommand):
    help = "Fetch fresh product photos from Unsplash/Pexels/Pixabay and replace the primary image."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--provider", choices=(*PROVIDER_ORDER, "auto"), default="auto")
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        self.keys = {
            "unsplash": os.environ.get("UNSPLASH_API_KEY", "").strip(),
            "pexels": os.environ.get("PEXELS_API_KEY", "").strip(),
            "pixabay": os.environ.get("PIXABAY_API_KEY", "").strip(),
        }
        missing = [name for name, key in self.keys.items() if not key]
        if missing:
            raise CommandError(f"Missing API keys in the environment: {', '.join(missing)}")

        queryset = Product.objects.active().select_related("category").order_by("pk")
        total = queryset.count()
        queryset = queryset[offset_slice(options)]
        if options["dry_run"]:
            self.stdout.write("dry run — nothing will be written")

        used_urls: set[str] = set()
        replaced = skipped = failed = 0

        for product in queryset:
            source = self.find_photo(product, options["provider"], used_urls)
            if source is None:
                self.stdout.write(self.style.WARNING(f"no photo  {product.slug}"))
                failed += 1
                continue
            used_urls.add(source[1])

            if options["dry_run"]:
                self.stdout.write(f"would use {product.slug} <- {source[0]}")
                replaced += 1
                continue

            try:
                blob = self.download(source[1])
                name = self.store(product, blob)
            except (urllib.error.URLError, UnidentifiedImageError, OSError) as exc:
                self.stdout.write(self.style.ERROR(f"failed    {product.slug}: {exc}"))
                failed += 1
                continue

            self.stdout.write(f"replaced  {product.slug} <- {source[0]} -> {name}")
            replaced += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"done: {replaced} replaced, {skipped} skipped, {failed} failed "
                f"of {len(queryset)} (catalogue has {total})"
            )
        )

    def find_photo(self, product: Product, provider: str, used: set[str]):
        query = self.query_for(product)
        providers = PROVIDER_ORDER if provider == "auto" else (provider,)
        for name in providers:
            key = self.keys[name]
            if not key:
                continue
            try:
                candidates = self.search(name, key, query)
            except (urllib.error.URLError, json.JSONDecodeError) as exc:
                self.stdout.write(self.style.WARNING(f"  {name} search failed: {exc}"))
                continue
            for url in candidates:
                if url not in used:
                    return name, url
        return None

    @staticmethod
    def query_for(product: Product) -> str:
        words = product.name.split()
        category = product.category.name if product.category else ""
        base = " ".join(words[:4])
        if category.lower().startswith(("house", "potter", "small", "big")):
            return f"{base} houseplant"
        if "seed" in category.lower() or "seed" in product.slug:
            return f"{base} seeds packet"
        if any(word in product.slug for word in ("pot", "basket", "planter", "vase")):
            return f"{base} ceramic pot plant"
        return base

    @staticmethod
    def search(provider: str, key: str, query: str) -> list[str]:
        if provider == "pixabay":
            url = f"{PIXABAY_SEARCH}?key={key}&q={urllib.parse.quote(query)}&image_type=photo&per_page=20&safesearch=true"
            payload = Command.fetch_json(url, {})
            return [hit.get("largeImageURL", "") for hit in payload.get("hits", []) if hit.get("largeImageURL")]

        if provider == "pexels":
            url = f"{PEXELS_SEARCH}?query={urllib.parse.quote(query)}&per_page=20&orientation=landscape"
            payload = Command.fetch_json(url, {"Authorization": key})
            photos = payload.get("photos", [])
            return [photo["src"]["large2x"] for photo in photos if photo.get("src", {}).get("large2x")]

        url = f"{UNSPLASH_SEARCH}?query={urllib.parse.quote(query)}&per_page=20"
        payload = Command.fetch_json(url, {"Authorization": f"Client-ID {key}"})
        results = payload.get("results", [])
        return [item["urls"]["regular"] for item in results if item.get("urls", {}).get("regular")]

    @staticmethod
    def fetch_json(url: str, headers: dict) -> dict:
        request = urllib.request.Request(url, headers={"User-Agent": "GreenShopSeed/1.0", **headers})
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))

    def download(self, url: str) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": "GreenShopSeed/1.0"})
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            blob = response.read()
        if not blob:
            raise OSError("empty body")
        return blob

    def store(self, product: Product, blob: bytes) -> str:
        image = Image.open(io.BytesIO(blob))
        image.load()
        image = image.convert("RGB")
        image.thumbnail((MAX_SOURCE_EDGE, MAX_SOURCE_EDGE), Image.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        buffer.seek(0)

        with transaction.atomic():
            primary = product.images.filter(is_primary=True).first()
            if primary is None:
                primary = product.images.order_by("pk").first()
            if primary is None:
                primary = ProductImage(product=product, is_primary=True)

            folder = Path(settings.MEDIA_ROOT) / "products"
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / f"{product.slug}.jpg"
            if destination.exists():
                destination.unlink()
            destination.write_bytes(buffer.getvalue())

            old_name = primary.image.name if primary.image else ""
            primary.image.name = f"products/{product.slug}.jpg"
            primary.alt = product.name
            primary.is_primary = True
            primary.save()

            if old_name and old_name != primary.image.name:
                stale = Path(settings.MEDIA_ROOT) / old_name
                if stale.exists():
                    stale.unlink()

        return primary.image.name


def offset_slice(options: dict) -> slice:
    start = options["offset"]
    stop = start + options["limit"] if options["limit"] else None
    return slice(start, stop)
