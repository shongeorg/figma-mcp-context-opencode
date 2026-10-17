"""End-to-end user-story tests for the GreenShop storefront (Playwright).

Runs against a live dev server — nothing here touches the Django test
runner, the database fixtures, ``core/tests.py`` or any other unit-test
module; every journey goes through the real HTML forms so the CSRF
tokens, redirects and flash messages are exercised exactly as a shopper
would hit them.

Run from ``backend/``:

    .\\.venv\\Scripts\\python.exe e2e\\test_user_stories.py

The base URL comes from the ``BASE_URL`` environment variable and
defaults to ``http://127.0.0.1:8000``.  One browser is shared by the
whole run; every test gets a fresh context (its own cookie jar, hence a
truly anonymous session) and closes it on teardown.  Tests are headless.
On failure a screenshot lands in ``e2e/artifacts/<test>.png``.
"""

from __future__ import annotations

import os
import re
import sys
import time
import unittest
from decimal import Decimal
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

DEFAULT_TIMEOUT_MS = 15_000

# Cart maths constants from orders/services.py.
SHIPPING_FLAT = Decimal("9.00")
FREE_SHIPPING_OVER = Decimal("120.00")


def shipping_for(subtotal: Decimal) -> Decimal:
    return Decimal("0.00") if subtotal >= FREE_SHIPPING_OVER else SHIPPING_FLAT


# ------------------------------------------------------------------ helpers --

def unique_username() -> str:
    """A username no previous run of the suite can have claimed."""
    return "pw_%.3f" % time.time()


def register(page: Page, *, first_name: str = "Playwright",
             password: str = "Leafy!Green123") -> tuple[str, str]:
    """Register a brand-new shopper through /register/ and return the credentials.

    The form is filled and submitted the way a visitor would; the CSRF
    token is whatever the rendered page handed us.  Registration signs
    the user in, so the page that comes back must be the home page with
    the user's name in the header.
    """
    username = unique_username()
    page.goto(f"{BASE_URL}/register/", wait_until="domcontentloaded")
    page.get_by_label("Username", exact=True).fill(username)
    page.get_by_label("First name", exact=True).fill(first_name)
    page.get_by_label("Last name", exact=True).fill("Botany")
    # The suite must be re-runnable, so the mailbox has to be unique too.
    page.get_by_label("Email", exact=True).fill(f"{username}@example.com")
    page.get_by_label("Phone (optional)", exact=True).fill("+15550100")
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_label("Repeat password", exact=True).fill(password)
    page.get_by_role("button", name="Register", exact=True).click()
    page.wait_for_url(re.compile(re.escape(BASE_URL) + r"/?$"))
    return username, password


def login(page: Page, username: str, password: str) -> None:
    """Sign in through /login/ the way the login page is meant to be used."""
    page.goto(f"{BASE_URL}/login/", wait_until="domcontentloaded")
    page.get_by_label("Username", exact=True).fill(username)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Login", exact=True).click()
    page.wait_for_url(re.compile(re.escape(BASE_URL) + r"/?$"))


def header_account_link(page: Page):
    """The header link that shows either "Login" or the user's first name."""
    return page.locator(".header-actions .btn-login")


def cart_link(page: Page, items: int | None = None):
    """The header cart link, matched by accessible name.

    Without a basket its accessible name is just "Cart"; with n units it
    "Cart, n item(s)" (from the screen-reader-only text — the visible
    badge itself is aria-hidden).  Scoped to the site header because the
    mobile appbar carries a second "Cart" link with no count.
    """
    if items is None:
        pattern = r"^Cart(, \d+ items?)?$"
    elif items == 0:
        pattern = r"^Cart$"
    elif items == 1:
        pattern = r"^Cart, 1 item$"
    else:
        pattern = rf"^Cart, {items} items$"
    return page.locator("header.site-header").get_by_role(
        "link", name=re.compile(pattern)
    )


def first_shop_product(page: Page):
    """Open the shop grid and return the first product card + its name."""
    page.goto(f"{BASE_URL}/shop/", wait_until="domcontentloaded")
    card = page.locator("ul.product-grid > li.product-card").first
    card.scroll_into_view_if_needed()
    name = card.locator(".product-card__title a").inner_text().strip()
    return card, name


def open_first_product(page: Page):
    """Navigate to the detail page of the first shop-grid product."""
    card, name = first_shop_product(page)
    card.locator(".product-card__title a").click()
    page.wait_for_url(re.compile(r".*/product/.+/$"))
    return name


def money(text: str) -> Decimal:
    """Parse "$1,234.50" out of an element's text."""
    match = re.search(r"\$([\d,]+\.\d{2})", text)
    assert match, f"no dollar amount in {text!r}"
    return Decimal(match.group(1).replace(",", ""))


# ---------------------------------------------------------------- test case --

class GreenShopUserStories(unittest.TestCase):
    """Eight shopper stories, each in its own browser context."""

    # One browser for the whole run; contexts are per-test for isolation.
    _playwright = None
    _browser = None

    @classmethod
    def setUpClass(cls):
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        if cls._browser is not None:
            cls._browser.close()
        if cls._playwright is not None:
            cls._playwright.stop()

    def setUp(self):
        self.context = self._browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(DEFAULT_TIMEOUT_MS)

    # -- screenshot-on-failure, wired through run() so it sees the result --
    # The snapshot needs a *live* page, but the result is only known after
    # run() returns — and cleanups would close the context by then.  So
    # run() owns the whole sequence: test → (result known) → screenshot →
    # context close, all in a finally block.

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
            self._mirrorOutput = True
        failures_before = len(result.failures)
        errors_before = len(result.errors)
        try:
            super().run(result)
        finally:
            failed = (
                len(result.failures) > failures_before
                or len(result.errors) > errors_before
            )
            if failed and getattr(self, "page", None) is not None:
                ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
                shot = ARTIFACTS_DIR / f"{self._testMethodName}.png"
                try:
                    self.page.screenshot(path=str(shot), full_page=True)
                    print(f"    [screenshot] {shot}", file=sys.stderr)
                except Exception as exc:  # pragma: no cover - best effort only
                    print(f"    [screenshot failed] {exc}", file=sys.stderr)
            context = getattr(self, "context", None)
            if context is not None:
                try:
                    context.close()
                except Exception:  # pragma: no cover - already gone
                    pass

    # ---------------------------------------------------------------- US 1 --

    def test_registration_lands_on_home_with_user_in_header(self):
        """US 1 — a brand-new shopper registers and is signed in immediately."""
        first_name = "Playwright"
        register(self.page, first_name=first_name)

        # Landed back on the home page…
        self.assertEqual(self.page.url, f"{BASE_URL}/")
        expect(
            self.page.get_by_role("heading", name=re.compile("Better Planet"))
        ).to_be_visible()
        # …the header greets the user by name instead of offering Login…
        account = header_account_link(self.page)
        expect(account).to_be_visible()
        self.assertIn(first_name, account.inner_text())
        self.assertNotIn("Login", account.inner_text())
        # …and the welcome flash message was rendered.
        expect(
            self.page.locator(".site-messages").get_by_text(f"Welcome, {first_name}!")
        ).to_be_visible()

    # ---------------------------------------------------------------- US 2 --

    def test_logout_login_roundtrip_and_get_logout_is_post_only(self):
        """US 2 — header logout (POST), re-login, and GET /logout/ is a no-op."""
        first_name = "Playwright"
        username, password = register(self.page, first_name=first_name)

        # Log out through the header's POST form ("Sign out" button).
        self.page.get_by_role("button", name="Sign out").click()
        self.page.wait_for_url(re.compile(re.escape(BASE_URL) + r"/?$"))
        expect(header_account_link(self.page)).to_have_text("Login")

        # Log back in with the same credentials via /login/.
        login(self.page, username, password)
        self.assertIn(first_name, header_account_link(self.page).inner_text())

        # Django's LogoutView is POST-only: a GET must NOT end the session.
        response = self.page.goto(f"{BASE_URL}/logout/", wait_until="domcontentloaded")
        self.assertEqual(
            response.status, 405,
            "GET /logout/ should be refused with 405 Method Not Allowed",
        )
        # The session survived the refused request.
        self.page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        self.assertIn(
            first_name, header_account_link(self.page).inner_text(),
            "GET /logout/ must not log the shopper out",
        )

    # ---------------------------------------------------------------- US 3 --

    def test_browse_shop_add_to_cart_and_place_order(self):
        """US 3 — the main journey: browse, product page, cart, checkout, order."""
        first_name = "Playwright"
        register(self.page, first_name=first_name)

        # Home -> Shop via the main navigation.
        self.page.locator("nav.primary-nav").get_by_role("link", name="Shop").click()
        self.page.wait_for_url(re.compile(r".*/shop/?$"))
        expect(
            self.page.get_by_role("heading", name="Shop", exact=True)
        ).to_be_visible()

        # Open the first product.
        product_name = open_first_product(self.page)
        expect(
            self.page.get_by_role("heading", level=1)
        ).to_have_text(product_name)

        # Choose a size if the page offers one (first enabled chip).
        size_buttons = self.page.locator(".sizes button:not([disabled])")
        if size_buttons.count() > 0:
            size_buttons.first.click()

        # Add to cart and watch the header badge.
        self.page.get_by_role(
            "button", name=re.compile("Add to cart|Buy Now")
        ).click()
        expect(
            self.page.locator(".site-messages")
            .get_by_text(re.compile(r"Added 1 × .+ to your cart\."))
        ).to_be_visible()
        expect(cart_link(self.page, 1)).to_be_visible()

        # Cart page: the line and the totals render.
        cart_link(self.page, 1).click()
        self.page.wait_for_url(re.compile(r".*/cart/?$"))
        line_row = self.page.locator("tbody tr", has_text=product_name).first
        expect(line_row).to_be_visible()
        unit_price = money(line_row.locator(".cell-price").inner_text())
        line_total = money(line_row.locator(".cell-total").inner_text())
        self.assertEqual(line_total, unit_price, "one unit: line total == unit price")

        expect(
            self.page.get_by_role("heading", name="Cart Totals")
        ).to_be_visible()
        totals = self.page.locator("dl.totals")
        totals_text = totals.inner_text()
        # The first amount rendered in the totals block is the subtotal.
        self.assertEqual(money(totals_text), line_total,
                         "subtotal equals the single line total")
        # The basket lists shipping as its own row, and its grand total
        # folds that charge in — the same arithmetic the checkout page
        # and the placed order use (both asserted below).
        ship = re.search(r"Ship(?:ing|ping)\s*\$([\d,]+\.\d{2})", totals_text)
        self.assertIsNotNone(ship, f"no shipping row in {totals_text!r}")
        self.assertEqual(
            Decimal(ship.group(1).replace(",", "")), shipping_for(line_total),
            "shipping row shows the real flat/freight charge",
        )
        expected_total = line_total + shipping_for(line_total)
        self.assertEqual(
            money(totals.locator(".total .value").inner_text()), expected_total,
            "cart grand total = subtotal − discount + shipping",
        )

        # Checkout: fill the billing form with valid data and place the order.
        self.page.get_by_role("link", name="Proceed To Checkout").click()
        self.page.wait_for_url(re.compile(r".*/checkout/?$"))
        expect(
            self.page.get_by_role("heading", name="Billing Address")
        ).to_be_visible()
        # The checkout page repeats the same maths before the order is placed:
        checkout_totals = self.page.locator("form.checkout dl.totals")
        self.assertEqual(money(checkout_totals.inner_text()), line_total,
                         "checkout subtotal matches the cart line")
        self.assertEqual(
            money(checkout_totals.locator(".total .value").inner_text()),
            expected_total,
            "checkout grand total = subtotal + shipping",
        )
        billing = self.page.locator("form.checkout .billing")
        # Labels on this form carry a trailing " *" for required fields.
        billing.get_by_label("Full Name").fill("Playwright Botany")
        billing.get_by_label("Email address").fill("shopper@example.com")
        billing.get_by_label("Country / Region").fill("USA")
        billing.get_by_label("Town / City").fill("Kyiv")
        billing.get_by_label("Street Address").fill("12 Fern Street")
        billing.get_by_label("State / Region").fill("Kyiv Region")
        billing.get_by_label("Zip").fill("01001")
        billing.get_by_label("Phone Number").fill("+380501112233")
        self.page.get_by_role("button", name="Place Order").click()

        # Redirected to the order confirmation page; number + totals visible.
        self.page.wait_for_url(re.compile(r".*/orders/GS-\d{6}-[0-9A-F]{4}/?$"))
        heading = self.page.get_by_role("heading", level=1).inner_text().strip()
        self.assertRegex(heading, r"^Order GS-\d{6}-[0-9A-F]{4}$")
        order_number = heading.removeprefix("Order ")
        expect(
            self.page.locator(".site-messages")
            .get_by_text(re.compile(rf"Order {re.escape(order_number)} received\."))
        ).to_be_visible()

        summary_list = self.page.locator(".account-main ul.order-list").last
        summary_text = summary_list.inner_text()
        self.assertIn("Subtotal", summary_text)
        self.assertEqual(money(summary_text), line_total,
                         "order subtotal matches the cart line")
        self.assertIn("Shipping", summary_text)
        self.assertEqual(
            money(summary_list.locator("li").last.inner_text()), expected_total,
            "order grand total matches the checkout total",
        )

        # The order also shows up in the history list, openable from there.
        self.page.get_by_role("link", name="All orders").click()
        self.page.wait_for_url(re.compile(r".*/orders/?$"))
        order_link = self.page.get_by_role("link", name=f"Order {order_number}")
        expect(order_link).to_be_visible()
        order_link.click()
        self.page.wait_for_url(re.compile(rf".*/orders/{re.escape(order_number)}/?$"))
        expect(
            self.page.get_by_role("heading", level=1)
        ).to_have_text(f"Order {order_number}")
        self.assertIn("Total", self.page.locator(".account-main").inner_text())

    # ---------------------------------------------------------------- US 4 --

    def test_cart_quantity_math_and_line_removal(self):
        """US 4 — two units of one product: quantity, line total, removal."""
        product_name = open_first_product(self.page)

        # Size chips (if offered) default to the first enabled one; keep it.
        # Ask for two units, then add.
        self.page.get_by_label("Quantity", exact=True).fill("2")
        self.page.get_by_role(
            "button", name=re.compile("Add to cart|Buy Now")
        ).click()
        expect(
            self.page.locator(".site-messages")
            .get_by_text(re.compile(r"Added 2 × .+ to your cart\."))
        ).to_be_visible()
        expect(cart_link(self.page, 2)).to_be_visible()

        # The cart page reflects the quantity and doubles the line total.
        cart_link(self.page, 2).click()
        self.page.wait_for_url(re.compile(r".*/cart/?$"))
        line_row = self.page.locator("tbody tr", has_text=product_name).first
        qty_input = line_row.get_by_role("spinbutton", name=re.compile("Quantity of"))
        self.assertEqual(qty_input.input_value(), "2")
        unit_price = money(line_row.locator(".cell-price").inner_text())
        line_total = money(line_row.locator(".cell-total").inner_text())
        self.assertEqual(line_total, unit_price * 2,
                         "line total must be quantity × unit price")
        totals = self.page.locator("dl.totals")
        self.assertEqual(money(totals.inner_text()), line_total,
                         "subtotal equals the doubled line total")

        # Remove the line; the basket reports itself empty again.
        line_row.get_by_role(
            "button",
            name=re.compile(rf"Remove {re.escape(product_name)} from the cart"),
        ).click()
        expect(
            self.page.locator(".site-messages")
            .get_by_text("Item removed from your cart.")
        ).to_be_visible()
        expect(self.page.get_by_text("Your cart is empty.")).to_be_visible()
        expect(cart_link(self.page, 0)).to_be_visible()

    # ---------------------------------------------------------------- US 5 --

    def test_review_submission_goes_to_moderation(self):
        """US 5 — a logged-in shopper reviews a product (kept pending)."""
        register(self.page)
        product_name = open_first_product(self.page)

        marker = f"E2E review marker {int(time.time())}"
        self.page.get_by_role("tab", name="Add a Review").click()
        panel = self.page.locator("#panel-add")
        expect(panel).to_be_visible()
        panel.get_by_label("Your rating").select_option("5")
        panel.get_by_label("Review title").fill("Lovely foliage")
        panel.get_by_label("Your review").fill(
            f"{marker}: thriving, well packed, arrived fast."
        )
        panel.get_by_role("button", name="Submit review").click()

        # The app holds new reviews for moderation — that is the real behaviour.
        expect(
            self.page.locator(".site-messages")
            .get_by_text("Thanks! Your review will appear once it is approved.")
        ).to_be_visible()
        # Therefore it must NOT be publicly visible yet, not even after a reload.
        self.page.reload(wait_until="domcontentloaded")
        self.assertNotIn(
            marker, self.page.content(),
            "a pending review must not be rendered publicly",
        )

    # ---------------------------------------------------------------- US 6 --

    def test_wishlist_add_show_remove(self):
        """US 6 — heart a product on the grid, see it in the wishlist, remove it."""
        register(self.page)
        card, product_name = first_shop_product(self.page)
        # The grid's heart button is hover-revealed (opacity 0 until then).
        card.hover()
        card.get_by_role("button", name=f"Add {product_name} to wishlist").click()
        expect(
            self.page.locator(".site-messages")
            .get_by_text(f"{product_name} added to your wishlist.")
        ).to_be_visible()

        self.page.goto(f"{BASE_URL}/wishlist/", wait_until="domcontentloaded")
        expect(self.page.get_by_role("heading", name="My Wishlist")).to_be_visible()
        wished_card = self.page.locator(
            "li.product-card",
            has=self.page.get_by_role("link", name=product_name, exact=True),
        )
        expect(wished_card).to_be_visible()

        # Same hover-revealed quick actions as on the shop grid.
        wished_card.hover()
        wished_card.get_by_role(
            "button", name=f"Remove {product_name} from wishlist"
        ).click()
        expect(
            self.page.locator(".site-messages")
            .get_by_text(f"{product_name} removed from your wishlist.")
        ).to_be_visible()
        expect(self.page.get_by_text("Your wishlist is empty.")).to_be_visible()

    # ---------------------------------------------------------------- US 7 --

    def test_add_to_cart_beyond_stock_is_blocked(self):
        """US 7a — ordering more than the shelf holds shows an error."""
        open_first_product(self.page)

        self.page.get_by_label("Quantity", exact=True).fill("999")
        self.page.get_by_role(
            "button", name=re.compile("Add to cart|Buy Now")
        ).click()

        # The view refuses with a flash error naming the real stock level…
        expect(
            self.page.locator(".site-messages")
            .get_by_text(re.compile(r"Only \d+ left in stock\."))
        ).to_be_visible()
        # …and nothing landed in the basket.
        expect(cart_link(self.page, 0)).to_be_visible()

    def test_checkout_with_empty_cart_redirects_to_cart(self):
        """US 7b — /checkout/ with an empty basket bounces to /cart/."""
        self.page.goto(f"{BASE_URL}/checkout/", wait_until="domcontentloaded")
        self.page.wait_for_url(re.compile(r".*/cart/?$"))
        expect(
            self.page.locator(".site-messages").get_by_text("Your cart is empty.")
        ).to_be_visible()
        # The empty basket offers a way back into the shop ("Continue
        # Shopping" appears both in the table and the summary aside).
        expect(
            self.page.get_by_role("link", name="Continue Shopping").first
        ).to_be_visible()

    # ---------------------------------------------------------------- US 8 --

    def test_blog_posts_render_and_posts_open_in_place(self):
        """US 8 — the blog: there is no /blog/ route in this app.

        The posts live as the "Our Blog Posts" section of the home page and
        their links anchor back to it, so this test pins down that real
        behaviour: /blog/ is a 404, the home section renders the seeded
        posts, and a post link keeps the shopper on that section.
        """
        response = self.page.goto(f"{BASE_URL}/blog/", wait_until="domcontentloaded")
        self.assertEqual(response.status, 404,
                         "the app defines no /blog/ route — it 404s today")

        self.page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        self.page.locator("nav.primary-nav").get_by_role("link", name="Blogs").click()
        self.page.wait_for_url(re.compile(r".*/#blog$"))

        blog_section = self.page.locator("#blog")
        expect(
            blog_section.get_by_role("heading", name="Our Blog Posts")
        ).to_be_visible()
        for title in (
            "Cactus & Succulent Care Tips",
            "Top 10 Succulents for Your Home",
            "The Basics of Caring for your Monstera",
        ):
            expect(
                blog_section.get_by_role("link", name=title)
            ).to_be_visible()

        # Opening a post: the link points back at the section itself (no
        # detail page exists), so the shopper stays on the home blog view.
        blog_section.get_by_role(
            "link", name="Cactus & Succulent Care Tips"
        ).click()
        self.page.wait_for_url(re.compile(r".*/#blog$"))
        expect(
            blog_section.get_by_role("heading", name="Our Blog Posts")
        ).to_be_visible()


# ----------------------------------------------------------------- summary --

class RecordingResult(unittest.TestResult):
    """Collects one (name, status, detail) record per test for the summary."""

    def __init__(self):
        super().__init__()
        self.records: list[tuple[str, str, str]] = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append((test._testMethodName, "PASS", ""))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append(
            (test._testMethodName, "FAIL", self._exc_info_to_string(err, test))
        )

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append(
            (test._testMethodName, "ERROR", self._exc_info_to_string(err, test))
        )


def main() -> int:
    # Artifacts describe THIS run — drop screenshots left by any earlier one.
    if ARTIFACTS_DIR.exists():
        for stale in ARTIFACTS_DIR.glob("*.png"):
            try:
                stale.unlink()
            except OSError:  # pragma: no cover - best effort only
                pass

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GreenShopUserStories)
    result = RecordingResult()
    suite.run(result)

    print()
    print("=" * 60)
    print("GreenShop E2E user stories — summary")
    print(f"base url: {BASE_URL}")
    print("=" * 60)
    for name, status, detail in result.records:
        print(f"{status:5s}  {name}")
        if detail:
            lines = detail.strip().splitlines()
            print(f"      {lines[-1] if lines else ''}")
            shot = ARTIFACTS_DIR / f"{name}.png"
            if shot.exists():
                print(f"      screenshot: {shot}")
    print("-" * 60)
    print(f"{len(result.records)} tests, "
          f"{sum(1 for _, s, _ in result.records if s == 'PASS')} passed, "
          f"{sum(1 for _, s, _ in result.records if s != 'PASS')} failed")
    print("=" * 60)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
