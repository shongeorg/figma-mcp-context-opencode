from __future__ import annotations

from django.core.signals import got_request_exception
from django.db import connection, transaction

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _rollback_open_transaction(sender, request, exception=None, **kwargs) -> None:
    if connection.in_atomic_block:
        connection.set_rollback(True)


got_request_exception.connect(
    _rollback_open_transaction,
    dispatch_uid="greenshop.rollback_open_transaction",
)


class AtomicWritesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in SAFE_METHODS:
            return self.get_response(request)
        with transaction.atomic():
            return self.get_response(request)
