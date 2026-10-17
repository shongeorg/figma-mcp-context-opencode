from __future__ import annotations

import os
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.db import connection, reset_queries  # noqa: E402
from django.test.client import Client  # noqa: E402
from django.test.utils import CaptureQueriesContext  # noqa: E402

ANON_PAGES = [
    ("/", "home"),
    ("/shop/", "shop"),
    ("/shop/category/house-plants/", "category"),
    ("/product/barberton-daisy/", "product"),
    ("/cart/", "cart (empty)"),
    ("/checkout/", "checkout (anon)"),
    ("/login/", "login"),
    ("/register/", "register"),
    ("/wishlist/", "wishlist (anon)"),
]


def timed(client, path: str, repeat: int) -> tuple[float, float, float]:
    walls = []
    with CaptureQueriesContext(connection) as ctx:
        for _ in range(repeat):
            started = time.perf_counter()
            response = client.get(path)
            walls.append(time.perf_counter() - started)
            assert response.status_code in (200, 302), (path, response.status_code)
        sql_time = sum(float(q.get("time", 0)) for q in ctx.captured_queries)
        queries = len(ctx.captured_queries) / repeat
    return sum(walls) / len(walls) * 1000, queries, sql_time / repeat * 1000


def show(name: str, wall: float, queries: float, sql: float) -> None:
    print(f"{name:<26} {wall:7.0f}ms {queries:8.0f} {sql:9.0f}ms")


def main() -> None:
    repeat = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    anon = Client(SERVER_NAME="localhost")

    for path, _ in ANON_PAGES:
        anon.get(path)

    print(f"{'page':<26} {'wall':>8} {'queries':>8} {'sql time':>10}")
    for path, name in ANON_PAGES:
        show(name, *timed(anon, path, repeat))

    user = Client(SERVER_NAME="localhost")
    ok = user.login(username="user", password="user")
    if not ok:
        print("\n!! demo user/user cannot log in — skipping auth pages")
        return

    from catalog.models import Product
    from orders import services as order_services

    product = Product.objects.active().first()
    request = user.get("/").wsgi_request
    order_services.add_to_cart(request, product, quantity=2)

    auth_pages = [
        ("/", "home (auth)"),
        ("/cart/", "cart (2 lines)"),
        ("/checkout/", "checkout (auth)"),
        ("/account/", "account"),
        ("/orders/", "orders"),
        ("/wishlist/", "wishlist (auth)"),
    ]
    for path, _ in auth_pages:
        user.get(path)

    print()
    for path, name in auth_pages:
        show(name, *timed(user, path, repeat))

    all_pages = [(p, n, anon) for p, n in ANON_PAGES] + [
        (p, n, user) for p, n in auth_pages
    ]
    worst = max(all_pages, key=lambda item: timed(item[2], item[0], 1)[1])
    client = worst[2]
    print(f"\nall queries — {worst[1]}:")
    reset_queries()
    with CaptureQueriesContext(connection) as ctx:
        client.get(worst[0])
    for i, q in enumerate(ctx.captured_queries, 1):
        sql = " ".join(q["sql"].split())
        print(f"  {i:2d}. {float(q['time']) * 1000:6.0f}ms  {sql[:125]}")


if __name__ == "__main__":
    main()
