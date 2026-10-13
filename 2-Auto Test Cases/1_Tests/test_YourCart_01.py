from playwright.sync_api import Locator, Page, expect


ALL_GAMES_URL = "https://www.paradoxinteractive.com/our-games/all-games"


def add_game(page: Page, card: Locator, expected_cart_count: int) -> None:
    card.hover()

    add_button = card.get_by_role(
        "button",
        name="Add to cart",
        exact=True,
    )
    expect(add_button).to_be_visible()
    add_button.click()

    toast = page.get_by_test_id("toast-list").get_by_text(
        "Added product to cart",
        exact=True,
    )
    expect(toast).to_be_visible()

    cart_number = page.locator('a[aria-label^="View cart"] div')
    expect(cart_number).to_have_text(str(expected_cart_count))

    # Espera a que desaparezca el aviso antes de comprobar el siguiente.
    expect(toast).to_be_hidden()


def test_your_cart_01_multiple_add_to_cart(page: Page) -> None:
    page.goto(ALL_GAMES_URL)
    expect(page.get_by_role("heading", name="ALL GAMES")).to_be_visible()

    # Según el HTML inspeccionado, las tarjetas comprables tienen data-ga_title
    # y un botón; las tarjetas "Coming soon" no tienen ese botón.
    purchasable_cards = page.locator("li[data-ga_title]:has(button)")
    assert purchasable_cards.count() >= 2, (
        "No hay dos juegos comprables disponibles en All Games"
    )

    first_card = purchasable_cards.nth(0)
    second_card = purchasable_cards.nth(1)

    first_title = first_card.get_attribute("data-ga_title")
    second_title = second_card.get_attribute("data-ga_title")
    assert first_title and second_title, "No se encontraron los títulos"
    assert first_title != second_title, "Se seleccionó dos veces el mismo juego"

    add_game(page, first_card, expected_cart_count=1)
    add_game(page, second_card, expected_cart_count=2)

    page.locator('a[aria-label^="View cart"]').click()

    expect(page.get_by_text(first_title, exact=True)).to_be_visible()
    expect(page.get_by_text(second_title, exact=True)).to_be_visible()