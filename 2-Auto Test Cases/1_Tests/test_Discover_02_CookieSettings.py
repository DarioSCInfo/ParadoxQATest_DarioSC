from playwright.sync_api import Page, expect

from CommonActions import DISCOVER_URL, open_page_with_cookie_consent

COOKIE_CATEGORIES = (
    "Targeting Cookies",
    "Performance Cookies",
    "Functional Cookies",
)


def get_cookie_panel(page: Page):
    return page.locator("#onetrust-pc-sdk")


def get_cookie_switch(page: Page, category: str):
    return get_cookie_panel(page).get_by_role(
        "switch",
        name=category,
        exact=True,
    )


def accept_initial_cookie_dialog(page: Page) -> None:
    expect(
        page.get_by_role(
            "button",
            name="Open Preferences",
            exact=True,
        )
    ).to_be_visible(timeout=10_000)


def open_cookie_settings(page: Page) -> None:
    panel = get_cookie_panel(page)

    if panel.is_visible():
        return

    page.get_by_role(
        "button",
        name="Open Preferences",
        exact=True,
    ).click()

    expect(panel).to_be_visible()


def set_cookie_switch(
    page: Page,
    category: str,
    enabled: bool,
) -> None:
    cookie_switch = get_cookie_switch(page, category)

    if cookie_switch.is_checked() != enabled:
        switch_id = cookie_switch.get_attribute("id")
        assert switch_id, f"No switch ID was found for {category}"

        switch_label = get_cookie_panel(page).locator(
            f'label[for="{switch_id}"]'
        )
        expect(switch_label).to_be_visible()
        switch_label.click()

    if enabled:
        expect(cookie_switch).to_be_checked()
    else:
        expect(cookie_switch).not_to_be_checked()


def expect_cookie_selection(
    page: Page,
    selection: dict[str, bool],
) -> None:
    for category, enabled in selection.items():
        cookie_switch = get_cookie_switch(page, category)

        if enabled:
            expect(cookie_switch).to_be_checked()
        else:
            expect(cookie_switch).not_to_be_checked()


def report_panel_closed(page: Page, reason: str) -> None:
    expect(get_cookie_panel(page)).to_be_hidden()
    print(f"Closed because {reason}.", flush=True)


def close_cookie_settings_with_x(page: Page) -> None:
    get_cookie_panel(page).locator("#close-pc-btn-handler").click()
    report_panel_closed(
        page,
        "the X button was clicked; unsaved changes were discarded",
    )


def test_discover_02_cookie_settings(page: Page) -> None:
    open_page_with_cookie_consent(page, DISCOVER_URL)
    accept_initial_cookie_dialog(page)
    open_cookie_settings(page)

    initial_selection = {
        category: get_cookie_switch(page, category).is_checked()
        for category in COOKIE_CATEGORIES
    }

    print("\n============================", flush=True)

    # Verify that each optional cookie switch can be turned on and off.
    for category in COOKIE_CATEGORIES:
        initial_state = initial_selection[category]
        set_cookie_switch(page, category, not initial_state)
        set_cookie_switch(page, category, initial_state)

    # Turn off all optional cookie categories.
    for category in COOKIE_CATEGORIES:
        set_cookie_switch(page, category, False)

    allow_all_button = page.get_by_role(
        "button",
        name="Allow All",
        exact=True,
    )
    expect(allow_all_button).to_be_visible()
    allow_all_button.click()
    report_panel_closed(page, "Allow All was selected")

    # Allow All should enable all optional categories.
    open_cookie_settings(page)
    all_enabled = {
        category: True
        for category in COOKIE_CATEGORIES
    }
    expect_cookie_selection(page, all_enabled)

    # Reject All should disable all optional categories.
    page.get_by_role(
        "button",
        name="Reject All",
        exact=True,
    ).click()
    report_panel_closed(page, "Reject All was selected")

    open_cookie_settings(page)
    all_disabled = {
        category: False
        for category in COOKIE_CATEGORIES
    }
    expect_cookie_selection(page, all_disabled)

    # Save a mixed selection with Confirm My Choices.
    saved_selection = {
        "Targeting Cookies": True,
        "Performance Cookies": False,
        "Functional Cookies": True,
    }

    for category, enabled in saved_selection.items():
        set_cookie_switch(page, category, enabled)

    page.get_by_role(
        "button",
        name="Confirm My Choices",
        exact=True,
    ).click()
    report_panel_closed(page, "Confirm My Choices was selected")

    # Close with X after changing a setting, then verify that it was not saved.
    open_cookie_settings(page)
    changed_category = "Targeting Cookies"

    set_cookie_switch(
        page,
        changed_category,
        not saved_selection[changed_category],
    )
    close_cookie_settings_with_x(page)

    open_cookie_settings(page)
    expect_cookie_selection(page, saved_selection)

    # Restore the preferences that were present when the test started.
    for category, enabled in initial_selection.items():
        set_cookie_switch(page, category, enabled)

    page.get_by_role(
        "button",
        name="Confirm My Choices",
        exact=True,
    ).click()
    report_panel_closed(
        page,
        "Confirm My Choices was selected to restore the initial preferences",
    )

    print("============================", flush=True)
