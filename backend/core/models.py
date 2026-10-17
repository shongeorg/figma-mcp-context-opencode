from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CLIENT = "client", "Client"

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.CLIENT,
        db_index=True,
    )
    phone = models.CharField(max_length=32, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    class Meta:
        ordering = ("-date_joined",)
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [models.Index(fields=["role", "-date_joined"])]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("core:account")


    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN


class Address(TimeStampedModel):
    class Label(models.TextChoices):
        HOME = "home", "Home"
        OFFICE = "office", "Office"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(max_length=16, choices=Label.choices, default=Label.HOME)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(
        max_length=32,
        blank=True,
        validators=[RegexValidator(r"^\+?[\d\s()-]{6,32}$", "Enter a valid phone number.")],
    )
    line1 = models.CharField(max_length=200, verbose_name="Address line")
    line2 = models.CharField(max_length=200, blank=True, verbose_name="Address line 2")
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True, verbose_name="State / region")
    postal_code = models.CharField(max_length=16, blank=True)
    country = models.CharField(max_length=80, default="USA")
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("-is_default", "label", "-created_at")
        verbose_name = "address"
        verbose_name_plural = "addresses"
        indexes = [models.Index(fields=["user", "-is_default"])]

    def __str__(self) -> str:
        return f"{self.label.title()} — {self.city}"

    def get_absolute_url(self):
        return reverse("core:address-detail", args=[self.pk])

    @property
    def one_line(self) -> str:
        parts = [self.line1, self.line2, self.city, self.region, self.postal_code, self.country]
        return ", ".join(p for p in parts if p)

    def save(self, *args, **kwargs):
        if self.is_default:
            (
                Address.objects.filter(user=self.user)
                .exclude(pk=self.pk)
                .update(is_default=False)
            )
        super().save(*args, **kwargs)


class Subscriber(TimeStampedModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "subscriber"
        verbose_name_plural = "subscribers"

    def __str__(self) -> str:
        return self.email
