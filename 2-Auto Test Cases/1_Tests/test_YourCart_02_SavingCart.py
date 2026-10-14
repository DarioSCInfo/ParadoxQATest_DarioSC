from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Page,
    Playwright,
    expect,
)

from CommonActions import (
    ALL_GAMES_URL,
    CART_URL,
    expect_product_added,
    open_cart_from_header,
    open_page_with_cookie_consent,
)


def launch_test_browser(
    playwright: Playwright,
    profile_dir: Path,
) -> BrowserContext:
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
    )


def get_regular_game_card(page: Page):
    return page.locator(
        'li[data-ga_item-list-name="All games"][data-ga_title]'
        ':has(a:has-text("Choose edition")), '
        'li[data-ga_item-list-name="All games"][data-ga_title]'
        ':has(button:has-text("Add to cart"))'
        ':not(:has(span[class*="ProductCard_original-price"]))'
    ).first

def add_one_regular_game(page: Page) -> str:
    open_page_with_cookie_consent(page, ALL_GAMES_URL)

    card = get_regular_game_card(page)
    expect(card).to_be_visible()
    card.hover()

    choose_edition = card.locator(
        'a:has-text("Choose edition")'
    )
    add_button = card.locator(
        'button:has-text("Add to cart")'
    )

    if choose_edition.count() and choose_edition.first.is_visible():
        choose_edition.first.click()

        edition_list = page.locator(
            'ul[class*="BuyPage_main-game-chapter"]'
        )
        expect(edition_list).to_be_visible()

        edition = page.locator(
            'ul[class*="BuyPage_main-game-chapter"]'
            '> li[class*="MainGame_card"]'
            ':not(:has(span[class*="PurchaseDetails_crossed-price"]))'
            ':has(button:has-text("Add to cart"))'
        ).first
        expect(edition).to_be_visible()

        title = edition.locator(
            'h3[class*="BuyCard_title"]'
        ).inner_text().strip()

        edition.locator(
            'button:has-text("Add to cart")'
        ).click()

    elif add_button.count() and add_button.first.is_visible():
        title = card.get_attribute("data-ga_title")
        assert title, "The product title was not found"
        add_button.first.click()

    else:
        raise AssertionError(
            "The selected game has no visible Add to cart "
            "or Choose edition action"
        )

    expect_product_added(page, expected_cart_count=1)

    print(f"Game added to cart: {title}", flush=True)
    return title


def open_and_check_cart(page: Page, expected_title: str) -> None:
    open_page_with_cookie_consent(page, CART_URL)

    expect(page.get_by_role("heading", name="Cart")).to_be_visible()
    expect(
        page.locator('div[class*="CartList_heading-container"] p')
    ).to_have_text("1 item")

    cart_items = page.locator(
        'ul[class*="CartList_line-items"] > li'
    )
    expect(cart_items).to_have_count(1)
    expect(cart_items.get_by_text(expected_title, exact=True)).to_be_visible()


def test_your_cart_02_saving_cart(tmp_path: Path, playwright: Playwright) -> None:
    profile_dir = tmp_path / "paradox-test-profile"
    print("\n============================", flush=True)
    # Reuse pytest-playwright's managed instance instead of starting a second
    # Sync Playwright context, which conflicts with pytest's active event loop.
    # Stage 1: keep one blank tab open and use a second tab for the store.
    context = launch_test_browser(playwright, profile_dir)

    try:
        blank_tab = context.pages[0]
        store_tab = context.new_page()

        game_title = add_one_regular_game(store_tab)

        store_tab.evaluate("window.scrollTo(0, 0)")

        open_cart_from_header(store_tab)

        open_and_check_cart(store_tab, game_title)

        print(
            "Stage 1 passed: the game is in the cart.",
            flush=True,
        )

        # Stage 2: close the cart tab and open the cart in a new tab.
        store_tab.close()

        second_cart_tab = context.new_page()
        open_and_check_cart(second_cart_tab, game_title)

        print(
            "Stage 2 passed: the cart was saved in a new tab.",
            flush=True,
        )
    finally:
        # Closing a persistent context also closes its browser.
        context.close()

    # Stage 3: reopen Chromium with the same profile and check the cart.
    context = launch_test_browser(playwright, profile_dir)

    try:
        restarted_tab = (
            context.pages[0]
            if context.pages
            else context.new_page()
        )
        open_and_check_cart(restarted_tab, game_title)

        print(
            "Stage 3 passed: the cart was saved after restarting "
            "the browser.",
            flush=True,
        )
    finally:
        context.close()
    print("============================", flush=True)
