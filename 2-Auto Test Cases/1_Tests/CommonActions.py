"""Shared Playwright actions for the Paradox store tests."""

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


DISCOVER_URL = "https://www.paradoxinteractive.com/our-games/discover"
ALL_GAMES_URL = "https://www.paradoxinteractive.com/our-games/all-games"
ON_SALE_URL = "https://www.paradoxinteractive.com/our-games/on-sale"
CART_URL = "https://www.paradoxinteractive.com/our-games/cart"

COOKIE_DIALOG_NAME = "Cookies and targeting"
COOKIE_ACCEPT_BUTTON_NAME = "OK"
PRODUCT_ADDED_MESSAGE = "Added product to cart"


def accept_cookies_if_present(page: Page) -> None:
    cookie_dialog = page.get_by_role("dialog", name=COOKIE_DIALOG_NAME)

    try:
        cookie_dialog.wait_for(state="visible", timeout=5_000)
    except PlaywrightTimeoutError:
        return

    cookie_dialog.get_by_role(
        "button",
        name=COOKIE_ACCEPT_BUTTON_NAME,
        exact=True,
    ).click()
    expect(cookie_dialog).to_be_hidden()


def open_page_with_cookie_consent(page: Page, url: str) -> None:
    page.goto(url)
    accept_cookies_if_present(page)


def expect_cart_count(page: Page, expected_count: int) -> None:
    cart_count = page.locator('a[aria-label^="View cart"] div')
    expect(cart_count).to_have_text(str(expected_count))


def expect_product_added(page: Page, expected_cart_count: int) -> None:
    toast = page.get_by_test_id("toast-list").get_by_text(
        PRODUCT_ADDED_MESSAGE,
        exact=True,
    )
    expect(toast).to_be_visible()
    expect_cart_count(page, expected_cart_count)
    expect(toast).to_be_hidden()


def open_cart_from_header(page: Page) -> None:
    page.locator('a[aria-label^="View cart"]').click()
