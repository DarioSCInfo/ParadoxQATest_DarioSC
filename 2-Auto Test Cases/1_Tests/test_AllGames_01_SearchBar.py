import re

from playwright.sync_api import (
    Locator,
    Page,
    expect,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


ALL_GAMES_URL = "https://www.paradoxinteractive.com/our-games/all-games"


def accept_cookies_if_present(page: Page) -> None:
    cookie_dialog = page.get_by_role("dialog", name="Cookies and targeting")
    try:
        cookie_dialog.wait_for(state="visible", timeout=5_000)
    except PlaywrightTimeoutError:
        return
    cookie_dialog.get_by_role("button", name="OK", exact=True).click()
    expect(cookie_dialog).to_be_hidden()

NON_PARADOX_SEARCHES = (
    "Minecraft",
    "Frostpunk",
    "Elden Ring",
    "Cyberpunk 2077",
    "Age of Empires",
)

PARADOX_SEARCHES = (
    "Stellaris",
    "Crusader Kings",
    "Age of Wonders",
    "Europa Universalis",
    "Cities: Skylines",
)


def get_search_box(page: Page) -> Locator:
    return page.get_by_role("searchbox", name="Search")


def clear_search_with_clear_all(page: Page) -> None:
    search_box = get_search_box(page)
    clear_all_button = page.get_by_role(
        "button",
        name=re.compile(r"^Clear all \(\d+\)$"),
    )

    expect(clear_all_button).to_be_visible()
    clear_all_button.click()
    expect(search_box).to_have_value("")


def add_first_search_result(
    page: Page,
    search_term: str,
    expected_cart_count: int,
) -> bool:
    cards = page.locator("li[data-ga_title]")
    result_card = cards.filter(has_text=search_term).first
    expect(result_card).to_be_visible()
    result_card.hover()

    add_button = result_card.get_by_role(
        "button",
        name="Add to cart",
        exact=True,
    )
    choose_edition = result_card.get_by_role(
        "link",
        name="Choose edition",
        exact=True,
    )
    read_more_link = result_card.get_by_role(
        "link",
        name=re.compile(
            r"Read more|More info|More information",
            re.IGNORECASE,
        ),
    )
    read_more_button = result_card.get_by_role(
        "button",
        name=re.compile(
            r"Read more|More info|More information",
            re.IGNORECASE,
        ),
    )

    if add_button.count() and add_button.first.is_visible():
        title = result_card.get_attribute("data-ga_title")
        assert title, "The product title was not found"
        add_button.first.click()

    elif choose_edition.count() and choose_edition.first.is_visible():
        choose_edition.first.click()

        edition_list = page.locator(
            'ul[class*="BuyPage_main-game-chapter"]'
        )
        expect(edition_list).to_be_visible()

        edition_card = page.locator(
            'ul[class*="BuyPage_main-game-chapter"]'
            '> li[class*="MainGame_card"]'
            ':has(button:has-text("Add to cart"))'
        ).first
        expect(edition_card).to_be_visible()

        title = edition_card.locator(
            'h3[class*="BuyCard_title"]'
        ).inner_text().strip()

        edition_card.get_by_role(
            "button",
            name="Add to cart",
            exact=True,
        ).click()

    elif (
        (read_more_link.count() and read_more_link.first.is_visible())
        or (read_more_button.count() and read_more_button.first.is_visible())
    ):
        print(
            f"Skipped '{search_term}': the result only has a Read More option.",
            flush=True,
        )
        return False

    else:
        print(
            f"Unrecognized result for '{search_term}': "
            f"{result_card.inner_text()}",
            flush=True,
        )
        print(
            f"Buttons: {result_card.get_by_role('button').all_text_contents()}",
            flush=True,
        )
        print(
            f"Links: {result_card.get_by_role('link').all_text_contents()}",
            flush=True,
        )
        return False

    toast = page.get_by_test_id("toast-list").get_by_text(
        "Added product to cart",
        exact=True,
    )
    expect(toast).to_be_visible()

    cart_count = page.locator('a[aria-label^="View cart"] div')
    expect(cart_count).to_have_text(str(expected_cart_count))
    expect(toast).to_be_hidden()

    print(
        f"Added to cart ({expected_cart_count}): {title}",
        flush=True,
    )

    search_box = get_search_box(page)
    if not search_box.count():
        page.go_back()
        expect(get_search_box(page)).to_have_value(search_term)

    return True


def test_all_games_01_search_bar(page: Page) -> None:
    page.goto(ALL_GAMES_URL)
    accept_cookies_if_present(page)

    search_box = get_search_box(page)

    print(
        "Technical limitation: the native X inside the search field is not "
        "independently exposed to Playwright. Searches are cleared with "
        "the Clear all button.",
        flush=True,
    )

    print("\n============================", flush=True)

    # Search for non-Paradox games and verify that no product purchase options appear.
    for search_term in NON_PARADOX_SEARCHES:
        search_box.fill(search_term)

        cards = page.locator("li[data-ga_title]")
        add_to_cart = cards.get_by_role(
            "button",
            name="Add to cart",
            exact=True,
        )
        choose_edition = cards.get_by_role(
            "link",
            name="Choose edition",
            exact=True,
        )
        more_info = cards.get_by_role(
            "link",
            name=re.compile(
                r"More info|More information",
                re.IGNORECASE,
            ),
        )

        expect(add_to_cart).to_have_count(0)
        expect(choose_edition).to_have_count(0)
        expect(more_info).to_have_count(0)

        print(
            f"No purchasable results found for: {search_term}",
            flush=True,
        )
        clear_search_with_clear_all(page)

    # Search for Paradox games and add the first purchasable result.
    added_count = 0
    print("============================", flush=True)

    for search_term in PARADOX_SEARCHES:
        search_box = get_search_box(page)
        search_box.fill(search_term)

        matching_card = page.locator("li[data-ga_title]").filter(
            has_text=search_term
        ).first
        expect(matching_card).to_be_visible()

        result_count = page.locator("li[data-ga_title]").count()
        print(
            f"Search '{search_term}': {result_count} result(s)",
            flush=True,
        )

        added = add_first_search_result(
            page,
            search_term,
            expected_cart_count=added_count + 1,
        )
        if added:
            added_count += 1

        clear_search_with_clear_all(page)

    assert added_count > 0, "No games were added to the cart"
    print("============================", flush=True)