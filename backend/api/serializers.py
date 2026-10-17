from __future__ import annotations

from decimal import Decimal

from .models import BlogPost


def money(value) -> str:
    if value is None:
        return "0.00"
    return str(Decimal(value).quantize(Decimal("0.01")))


def serialize_category_node(category, children, product_count: int) -> dict:
    return {
        "id": category.pk,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "image": category.image.url if category.image else None,
        "product_count": product_count,
        "children": children,
    }


def serialize_size(size, product_count: int | None = None) -> dict:
    row = {
        "id": size.pk,
        "name": size.name,
        "slug": size.slug,
        "ordering": size.ordering,
    }
    if product_count is not None:
        row["product_count"] = product_count
    return row


def serialize_tag(tag) -> dict:
    return {"id": tag.pk, "name": tag.name, "slug": tag.slug}


def serialize_category_summary(category) -> dict | None:
    if category is None:
        return None
    parent = category.parent
    return {
        "id": category.pk,
        "name": category.name,
        "slug": category.slug,
        "parent": (
            {"id": parent.pk, "name": parent.name, "slug": parent.slug}
            if parent is not None
            else None
        ),
    }


def serialize_product_summary(product) -> dict:
    image = product.primary_image
    return {
        "id": product.pk,
        "name": product.name,
        "slug": product.slug,
        "sku": product.sku,
        "category": serialize_category_summary(product.category),
        "price": money(product.price),
        "old_price": money(product.old_price) if product.old_price is not None else None,
        "is_on_sale": product.is_on_sale,
        "discount_percent": product.discount_percent,
        "stock": product.stock,
        "is_featured": product.is_featured,
        "is_new": product.is_new,
        "rating": money(product.rating),
        "reviews_count": product.reviews_count,
        "image": image.image.url if image else None,
        "tags": [tag.slug for tag in product.tags.all()],
    }


def serialize_product_size(product_size) -> dict:
    return {
        "id": product_size.pk,
        "size": {
            "id": product_size.size.pk,
            "name": product_size.size.name,
            "slug": product_size.size.slug,
        },
        "price": money(product_size.price),
        "price_delta": money(product_size.price_delta),
        "stock": product_size.stock,
        "is_active": product_size.is_active,
    }


def serialize_product_image(image) -> dict:
    return {
        "id": image.pk,
        "url": image.image.url,
        "alt": image.alt,
        "is_primary": image.is_primary,
        "ordering": image.ordering,
    }


def serialize_product_detail(product, reviews) -> dict:
    row = serialize_product_summary(product)
    row.update({
        "short_description": product.short_description,
        "description": product.description,
        "sizes": [serialize_product_size(ps) for ps in product.get_sizes()],
        "images": [serialize_product_image(img) for img in product.images.all()],
        "reviews": list(reviews),
    })
    return row


def serialize_blog_post(post: BlogPost) -> dict:
    return {
        "id": post.pk,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "body": post.body,
        "tags": post.tags_list,
        "image": post.image.url if post.image else None,
        "is_published": post.is_published,
        "published_at": post.published_at.isoformat() if post.published_at else None,
    }


def serialize_review(review, include_product: bool = True) -> dict:
    row = {
        "id": review.pk,
        "user": {
            "id": review.user_id,
            "username": review.user.username,
        },
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "is_approved": review.is_approved,
        "created_at": review.created_at.isoformat(),
    }
    if include_product:
        row["product"] = {
            "id": review.product_id,
            "name": review.product.name,
            "slug": review.product.slug,
        }
    return row


def serialize_cart_line(line) -> dict:
    return {
        "id": line.pk,
        "product": serialize_product_summary(line.product),
        "size": (
            {
                "id": line.size.pk,
                "size_id": line.size.size_id,
                "name": line.size.size.name,
                "price_delta": money(line.size.price_delta),
            }
            if line.size_id and line.size is not None
            else None
        ),
        "quantity": line.quantity,
        "unit_price": money(line.unit_price),
        "line_total": money(line.line_total),
    }


def serialize_order(order, include_items: bool = True) -> dict:
    row = {
        "id": order.pk,
        "number": order.number,
        "status": order.status,
        "full_name": order.full_name,
        "email": order.email,
        "phone": order.phone,
        "address_line": order.address_line,
        "city": order.city,
        "region": order.region,
        "postal_code": order.postal_code,
        "country": order.country,
        "note": order.note,
        "payment_method": order.payment_method,
        "is_paid": order.is_paid,
        "coupon_code": order.coupon_code,
        "subtotal": money(order.subtotal),
        "discount": money(order.discount),
        "shipping": money(order.shipping),
        "total": money(order.total),
        "created_at": order.created_at.isoformat(),
        "items_count": sum(item.quantity for item in order.items.all()),
    }
    if include_items:
        row["items"] = [
            {
                "id": item.pk,
                "product_name": item.product_name,
                "product_slug": item.product_slug,
                "size_name": item.size_name,
                "sku": item.sku,
                "image_url": item.image_url,
                "quantity": item.quantity,
                "unit_price": money(item.unit_price),
                "line_total": money(item.line_total),
            }
            for item in order.items.all()
        ]
    return row


def serialize_user(user) -> dict:
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "is_staff": user.is_staff,
        "phone": user.phone,
    }
