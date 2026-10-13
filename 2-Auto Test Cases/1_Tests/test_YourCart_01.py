from decimal import Decimal

from playwright.sync_api import (
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
)

ALL_GAMES_URL = "https://www.paradoxinteractive.com/our-games/all-games"
NUMBER_OF_GAMES = 3

def add_game( page: Page, card: Locator, expected_cart_count: int,) -> tuple[str, Decimal]:
    title = card.get_attribute("data-ga_title")
    price_text = card.get_attribute("data-ga_price")

    assert title, "No se encontró el título del juego"
    assert price_text, f"No se encontró el precio de {title}"

    card.hover()
    add_button = card.locator('button[url]:has-text("Add to cart")')
    expect(add_button).to_be_visible()
    add_button.click()

    toast = page.get_by_test_id("toast-list").get_by_text(
        "Added product to cart",
        exact=True,
    )
    expect(toast).to_be_visible()

    cart_number = page.locator('a[aria-label^="View cart"] div')
    expect(cart_number).to_have_text(str(expected_cart_count))
    expect(toast).to_be_hidden()

    return title, Decimal(price_text)

def test_your_cart_01_multiple_add_to_cart(page: Page) -> None:
    page.goto(ALL_GAMES_URL)

    cookie_dialog = page.get_by_role("dialog", name="Cookies and targeting")
    try:
        cookie_dialog.wait_for(state="visible", timeout=5000)
    except PlaywrightTimeoutError:
        pass
    else:
        cookie_dialog.get_by_role("button", name="OK", exact=True).click()
        expect(cookie_dialog).to_be_hidden()

    expect(page.get_by_role("heading", name="ALL GAMES")).to_be_visible()

    purchasable_cards = page.locator(
        'li[data-ga_title]:has(button[url]:has-text("Add to cart"))'
    )
    assert purchasable_cards.count() >= NUMBER_OF_GAMES, (
        f"No hay {NUMBER_OF_GAMES} juegos con botón Add to cart"
    )

    added_games = []

    for index in range(NUMBER_OF_GAMES):
        added_games.append(
            add_game(
                page,
                purchasable_cards.nth(index),
                expected_cart_count=index + 1,
            )
        )

    assert len(added_games) == NUMBER_OF_GAMES, (
        f"Se añadieron {len(added_games)} juegos; "
        f"se esperaban {NUMBER_OF_GAMES}"
    )

    print("\n===============", flush=True)
    for title, _ in added_games:
        print(title, flush=True)
    print("===============", flush=True)

    expected_total = sum(
        (price for _, price in added_games),
        start=Decimal("0.00"),
    )
    expected_total_text = f"{expected_total:.2f} EUR"

    page.evaluate("window.scrollTo(0, 0)")
    page.locator('a[aria-label^="View cart"]').click()

    expect(page.get_by_role("heading", name="Cart")).to_be_visible()

    expect(
        page.locator('div[class*="CartList_heading-container"] p')
    ).to_have_text(f"{NUMBER_OF_GAMES} items")

    cart_items = page.locator(
        'ul[class*="CartList_line-items"] > li'
    )
    expect(cart_items).to_have_count(NUMBER_OF_GAMES)

    expect(page.get_by_role("heading", name="Summary")).to_be_visible()

    subtotal_value = page.get_by_text("Subtotal", exact=True).locator(
        "xpath=following-sibling::span"
    )
    total_value = page.get_by_text("Total", exact=True).locator(
        "xpath=following-sibling::span"
    )

    expect(subtotal_value).to_have_text(expected_total_text)
    expect(total_value).to_have_text(expected_total_text)

    print(f"Cart summary verified: {expected_total_text}", flush=True)