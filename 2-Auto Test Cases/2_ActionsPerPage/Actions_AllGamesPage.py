"""
IMPORTANT:
This file must not contain any test plan steps or test cases.
It only contains the actions and behaviours associated with the file name page.
"""

from playwright.sync_api import Page, expect

class AllGamesPage:
    URL = "https://www.paradoxinteractive.com/our-games/all-games"

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> None:
        self.page.goto(self.URL)
        expect(
            self.page.get_by_role("heading", name="ALL GAMES")
        ).to_be_visible()

    def add_two_games(self) -> tuple[str, str]:
        # Las tarjetas comprables tienen un botón; las de "Coming soon" no.
        cards = self.page.locator("li[data-ga_title]:has(button)")
        assert cards.count() >= 2, "No hay dos juegos comprables disponibles"

        first_card = cards.nth(0)
        second_card = cards.nth(1)

        first_title = first_card.get_attribute("data-ga_title")
        second_title = second_card.get_attribute("data-ga_title")
        assert first_title and second_title, "No se encontraron los títulos"
        assert first_title != second_title, "Se seleccionó dos veces el mismo juego"

        toast_message = self.page.get_by_test_id("toast-list").get_by_text(
            "Added product to cart",
            exact=True,
        )
        cart_number = self.page.locator(
            'a[aria-label^="View cart"] div'
        )

        first_card.hover()
        first_card.get_by_role(
            "button", name="Add to cart", exact=True
        ).click()
        expect(toast_message).to_be_visible()
        expect(cart_number).to_have_text("1")

        # Espera a que desaparezca el primer aviso antes del segundo clic.
        expect(toast_message).to_be_hidden()

        second_card.hover()
        second_card.get_by_role(
            "button", name="Add to cart", exact=True
        ).click()
        expect(toast_message).to_be_visible()
        expect(cart_number).to_have_text("2")

        return first_title, second_title