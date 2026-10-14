import re
from decimal import Decimal
from playwright.sync_api import (
    Locator,
    Page,
    expect,
)

from CommonActions import (
    ALL_GAMES_URL,
    ON_SALE_URL,
    expect_cart_count,
    expect_product_added,
    open_cart_from_header,
    open_page_with_cookie_consent,
)


EXPECTED_ITEMS_BEFORE_REMOVAL = 2
EXPECTED_ITEMS_AFTER_REMOVAL = 1
ERROR_MARGIN = Decimal("0.05")

def parse_euro_amount(text: str) -> Decimal:
    normalized_text = text.replace("−", "-")
    match = re.search(r"-?[\d.,]+", normalized_text)
    assert match, f"Could not parse the amount from: {text}"
    return Decimal(match.group(0).replace(",", "."))

def expect_amount_within_margin(
    locator: Locator,
    expected: Decimal,
    label: str,
) -> None:
    margin_in_cents = int(ERROR_MARGIN * 100)
    accepted_amounts = "|".join(
        re.escape(f"{expected + Decimal(cents) / 100:.2f} EUR")
        for cents in range(-margin_in_cents, margin_in_cents + 1)
    )

    expect(locator).to_have_text(
        re.compile(rf"^(?:{accepted_amounts})$"),
        timeout=15_000,
    )

def get_card_price(card: Locator) -> Decimal:
    price = card.get_attribute("data-ga_price")
    assert price, "The product price was not found"
    return Decimal(price)

def get_card_original_price(card: Locator) -> Decimal:
    original_price = card.locator(
        'span[class*="ProductCard_original-price"]'
    )
    price_text = original_price.text_content()

    assert price_text and price_text.strip(), (
        "The product's original price was not found"
    )

    return parse_euro_amount(price_text)

def get_listing_card(
    page: Page,
    item_list_name: str,
    expect_discount: bool,
) -> Locator:
    base = (
        f'li[data-ga_item-list-name="{item_list_name}"][data-ga_title]'
    )
    choose_edition = f'{base}:has(a:has-text("Choose edition"))'

    if expect_discount:
        add_to_cart = (
            f'{base}:has(button:has-text("Add to cart"))'
            ':has(span[class*="ProductCard_original-price"])'
        )
    else:
        add_to_cart = (
            f'{base}:has(button:has-text("Add to cart"))'
            ':not(:has(span[class*="ProductCard_original-price"]))'
        )

    return page.locator(f"{choose_edition}, {add_to_cart}").first

def add_from_listing(
    page: Page,
    item_list_name: str,
    expect_discount: bool,
    expected_cart_count: int,
) -> tuple[str, Decimal, Decimal]:
    card = get_listing_card(page, item_list_name, expect_discount)
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

        edition_base = (
            'ul[class*="BuyPage_main-game-chapter"]'
            '> li[class*="MainGame_card"]'
        )

        if expect_discount:
            edition = page.locator(
                f"{edition_base}"
                ':has(span[class*="PurchaseDetails_crossed-price"])'
                ':has(button:has-text("Add to cart"))'
            ).first
        else:
            edition = page.locator(
                f"{edition_base}"
                ':not(:has(span[class*="PurchaseDetails_crossed-price"]))'
                ':has(button:has-text("Add to cart"))'
            ).first

        expect(edition).to_be_visible()

        title = edition.locator(
            'h3[class*="BuyCard_title"]'
        ).inner_text().strip()

        price_text = edition.locator(
            'div[class*="PurchaseDetails_price-wrapper"] p.heading-l'
        ).inner_text()
        current_price = parse_euro_amount(price_text)

        original_price_locator = edition.locator(
            'span[class*="PurchaseDetails_crossed-price"]'
        )

        if expect_discount:
            expect(original_price_locator).to_be_visible()
            original_price = parse_euro_amount(
                original_price_locator.inner_text()
            )
        else:
            original_price = current_price

        edition.locator(
            'button:has-text("Add to cart")'
        ).click()

    elif add_button.count() and add_button.first.is_visible():
        title = card.get_attribute("data-ga_title")
        assert title, "The product title was not found"

        current_price = get_card_price(card)
        original_price_locator = card.locator(
            'span[class*="ProductCard_original-price"]'
        )

        if expect_discount:
            original_price = get_card_original_price(card)
        else:
            assert original_price_locator.count() == 0, (
                f"The All Games product is discounted: {title}"
            )
            original_price = current_price

        add_button.first.click()

    else:
        links = card.locator("a").all_inner_texts()
        buttons = card.locator("button").all_inner_texts()
        raise AssertionError(
            f"Could not identify the action for {item_list_name}. "
            f"Links: {links}; buttons: {buttons}"
        )

    if expect_discount:
        assert current_price < original_price, (
            f"The product is not discounted: {title}"
        )
    else:
        assert current_price == original_price, (
            f"Expected a product without a discount: {title}"
        )

    expect_product_added(page, expected_cart_count)

    print(
        f"{expected_cart_count}/{EXPECTED_ITEMS_BEFORE_REMOVAL} "
        f"{title} [{item_list_name}]",
        flush=True,
    )

    return title, current_price, original_price

def expect_cart_summary(
    page: Page,
    expected_subtotal: Decimal,
    expected_discount: Decimal,
    expected_total: Decimal,
) -> None:
    subtotal = page.get_by_text("Subtotal", exact=True).locator(
        "xpath=following-sibling::span"
    )
    expect_amount_within_margin(
        subtotal,
        expected_subtotal,
        "Subtotal",
    )

    discount_label = page.get_by_text("Discount", exact=True)

    if expected_discount > 0:
        expect(discount_label).to_be_visible()
        discount = discount_label.locator(
            "xpath=following-sibling::span"
        )
        expect_amount_within_margin(
            discount,
            -expected_discount,
            "Discount",
        )
    elif discount_label.count():
        discount = discount_label.locator(
            "xpath=following-sibling::span"
        )
        expect_amount_within_margin(
            discount,
            Decimal("0.00"),
            "Discount",
        )

    total = page.get_by_text("Total", exact=True).locator(
        "xpath=following-sibling::span"
    )
    expect_amount_within_margin(total, expected_total, "Total")

def test_your_cart_01_add_regular_and_sale_game(page: Page) -> None:
    open_page_with_cookie_consent(page, ALL_GAMES_URL)

    print("\n============================", flush=True)

    regular_title, regular_price, regular_original_price = add_from_listing(
        page,
        item_list_name="All games",
        expect_discount=False,
        expected_cart_count=1,
    )

    open_page_with_cookie_consent(page, ON_SALE_URL)

    sale_title, sale_price, original_sale_price = add_from_listing(
        page,
        item_list_name="On Sale",
        expect_discount=True,
        expected_cart_count=2,
    )

    print("============================", flush=True)

    expected_subtotal = regular_original_price + original_sale_price
    expected_discount = original_sale_price - sale_price
    expected_total = regular_price + sale_price

    page.evaluate("window.scrollTo(0, 0)")
    open_cart_from_header(page)

    expect(page.get_by_role("heading", name="Cart")).to_be_visible()
    expect(
        page.locator('div[class*="CartList_heading-container"] p')
    ).to_have_text(f"{EXPECTED_ITEMS_BEFORE_REMOVAL} items")

    cart_items = page.locator(
        'ul[class*="CartList_line-items"] > li'
    )
    expect(cart_items).to_have_count(EXPECTED_ITEMS_BEFORE_REMOVAL)
    expect(page.get_by_role("heading", name="Summary")).to_be_visible()

    expect_cart_summary(
        page,
        expected_subtotal=expected_subtotal,
        expected_discount=expected_discount,
        expected_total=expected_total,
    )

    page.get_by_role(
        "button",
        name=f"Remove {sale_title} from cart",
        exact=True,
    ).click()

    expect(
        page.locator('div[class*="CartList_heading-container"] p')
    ).to_have_text(f"{EXPECTED_ITEMS_AFTER_REMOVAL} item")
    expect(cart_items).to_have_count(EXPECTED_ITEMS_AFTER_REMOVAL)

    expect_cart_count(page, EXPECTED_ITEMS_AFTER_REMOVAL)

    expect_cart_summary(
        page,
        expected_subtotal=regular_price,
        expected_discount=Decimal("0.00"),
        expected_total=regular_price,
    )

    print("Games in the cart", flush=True)
    print(regular_title, flush=True)
    print(f"{sale_title} (This item was deleted)", flush=True)
    print(f"Total price: {expected_total:.2f} EUR", flush=True)
    print(
        f"Total price after removing the sale item: "
        f"{regular_price:.2f} EUR",
        flush=True,
    )
    print("============================", flush=True)
