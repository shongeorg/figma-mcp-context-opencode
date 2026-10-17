from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel
from core.utils import unique_slugify


class BlogPost(TimeStampedModel):
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    excerpt = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to="blog/", blank=True, null=True)

    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-published_at", "-created_at")
        verbose_name = "blog post"
        verbose_name_plural = "blog posts"
        indexes = [models.Index(fields=["is_published", "-published_at"])]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title, max_length=180)
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("api:blog-detail", args=[self.slug])

    @property
    def tags_list(self) -> list[str]:
        tags = self.tags or []
        return [str(tag) for tag in tags] if isinstance(tags, list) else []

    @property
    def is_live(self) -> bool:
        if not self.is_published:
            return False
        if self.published_at and self.published_at > timezone.now():
            return False
        return True
