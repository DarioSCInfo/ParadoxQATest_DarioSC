import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect


ALL_GAMES_URL = "https://www.paradoxinteractive.com/our-games/all-games"


def accept_cookies_if_present(page: Page) -> None:
    cookie_dialog = page.get_by_role("dialog", name="Cookies and targeting")
    try:
        cookie_dialog.wait_for(state="visible", timeout=5_000)
    except PlaywrightTimeoutError:
        return
    cookie_dialog.get_by_role("button", name="OK", exact=True).click()
    expect(cookie_dialog).to_be_hidden()

FILTER_GROUPS = (
    "Brand",
    "Product Type",
    "OS Compatibility",
    "Offers",
    "Platform",
    "Genre",
)

def get_filter_group(page: Page, filter_name: str):
    return page.locator(
        f'h2:text-is("{filter_name}") + div[role="group"]'
    )

def test_all_games_personalized_filters(page: Page) -> None:
    page.goto(ALL_GAMES_URL)
    accept_cookies_if_present(page)

    page.get_by_role("button", name="Filter").click()

    # Test each filter option individually.
    for filter_name in FILTER_GROUPS:
        filter_group = get_filter_group(page, filter_name)
        expect(filter_group).to_be_visible()

        more_button = filter_group.get_by_role(
            "button",
            name="More",
            exact=True,
        )

        if more_button.count():
            more_button.click()

        checkboxes = filter_group.locator('input[type="checkbox"]')
        labels = filter_group.locator("label")

        assert checkboxes.count() > 0, (
            f"No filter options were found in the {filter_name} group"
        )
        assert labels.count() == checkboxes.count(), (
            f"The number of labels does not match the number of "
            f"checkboxes in the {filter_name} group"
        )

        for index in range(checkboxes.count()):
            checkbox = checkboxes.nth(index)
            label = labels.nth(index)
            option_name = label.inner_text().strip()

            expect(checkbox).not_to_be_checked()
            label.click()
            expect(checkbox).to_be_checked()

            print(
                f"Individual filter selected: "
                f"{filter_name} - {option_name}",
                flush=True,
            )

            label.click()
            expect(checkbox).not_to_be_checked()

            print(
                f"Individual filter cleared: "
                f"{filter_name} - {option_name}",
                flush=True,
            )

    # Select all filter options together.
    print("Selecting all filters together", flush=True)

    for filter_name in FILTER_GROUPS:
        filter_group = get_filter_group(page, filter_name)
        checkboxes = filter_group.locator('input[type="checkbox"]')
        labels = filter_group.locator("label")

        for index in range(checkboxes.count()):
            checkbox = checkboxes.nth(index)

            if not checkbox.is_checked():
                labels.nth(index).click()

            expect(checkbox).to_be_checked()

    print("All filter options are selected", flush=True)

    # Verify the Clear all counter, clear the filters, and check they are unchecked.
    selected_filter_count = 0

    for filter_name in FILTER_GROUPS:
        filter_group = get_filter_group(page, filter_name)
        checkboxes = filter_group.locator('input[type="checkbox"]')

        for index in range(checkboxes.count()):
            if checkboxes.nth(index).is_checked():
                selected_filter_count += 1

    clear_all_button = page.get_by_role(
        "button",
        name=re.compile(r"^Clear all \(\d+\)$"),
    )

    expect(clear_all_button).to_have_text(
        f"Clear all ({selected_filter_count})"
    )
    clear_all_button.click()
    expect(clear_all_button).to_be_hidden()

    for filter_name in FILTER_GROUPS:
        filter_group = get_filter_group(page, filter_name)
        checkboxes = filter_group.locator('input[type="checkbox"]')

        for index in range(checkboxes.count()):
            expect(checkboxes.nth(index)).not_to_be_checked()

    print("All filters were cleared", flush=True)