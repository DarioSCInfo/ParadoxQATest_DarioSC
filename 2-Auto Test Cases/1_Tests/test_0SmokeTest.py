from playwright.sync_api import Page, expect

def test_playwright_can_start(page: Page) -> None:
    page.set_content("<h1>Playwright listo</h1>")
    expect(page.get_by_role("heading", name="Playwright listo")).to_be_visible()