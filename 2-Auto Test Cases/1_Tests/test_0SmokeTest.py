import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


MINIMUM_PYTHON_VERSION = (3, 10)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def get_pinned_version(package_name: str) -> str:
    """Read a package's exact pinned version from requirements.txt."""
    requirements_file = PROJECT_ROOT / "requirements.txt"
    for line in requirements_file.read_text(encoding="utf-8").splitlines():
        requirement = line.strip()
        if requirement.startswith(f"{package_name}=="):
            return requirement.split("==", maxsplit=1)[1].strip()

    pytest.fail(
        f"No exact version pin for {package_name} was found in "
        f"{requirements_file}"
    )


def test_project_runtime_versions() -> None:

    print("\n============================", flush=True)

    python_version = sys.version_info[:3]
    python_version_text = ".".join(map(str, python_version))
    minimum_python_text = ".".join(map(str, MINIMUM_PYTHON_VERSION))

    print(f"Python: {python_version_text}", flush=True)
    assert python_version >= MINIMUM_PYTHON_VERSION, (
        f"Python {minimum_python_text} or newer is required; "
        f"found {python_version_text}"
    )

    for package_name in ("pytest", "playwright"):
        expected_version = get_pinned_version(package_name)
        try:
            installed_version = version(package_name)
        except PackageNotFoundError:
            pytest.fail(f"{package_name} is not installed in this environment")

        print(f"{package_name}: {installed_version}", flush=True)
        assert installed_version == expected_version, (
            f"{package_name} {expected_version} is required by requirements.txt; "
            f"found {installed_version}"
        )
    print("============================", flush=True)


def test_playwright_can_start(page: Page) -> None:
    page.set_content("<h1>Playwright listo</h1>")
    expect(page.get_by_role("heading", name="Playwright listo")).to_be_visible()
    print("\n============================", flush=True)