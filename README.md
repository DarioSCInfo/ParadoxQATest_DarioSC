# PARADOX Store and Shopping Test Suite

Automated UI tests for browsing the PARADOX store and using its shopping cart. The project includes a small desktop app for setup and test execution, plus commands for running everything from PowerShell or Command Prompt.

## Quick start with the desktop app

1. Copy or extract the project folder onto the computer.
2. Open **PARADOX store and shopping Tool.exe**
3. Click **Setup** and wait for the setup window to finish. Press a key when prompted to close it.
4. Click **Smoke Test** to check that the required Python and Playwright components are available.
5. Use **Test 01** through **Test 05** to run a functional test, or click **Full Test** to run all five functional tests in sequence.

The desktop app opens a browser window while the functional tests run. **Full Test** does not include the Smoke Test.

## Setup and run from a terminal

Open PowerShell or Command Prompt in the project root folder, the folder containing setup.cmd, and run:

~~~powershell
.\setup.cmd
~~~

The setup script creates a project-specific virtual environment, installs pytest and Playwright, and downloads Chromium. It requires an internet connection. It uses an existing Python 3.10 or newer installation; if none is found, it attempts to install Python 3.12 with winget.

### Run the smoke test

~~~powershell
.\.venv\Scripts\python.exe -m pytest "2-Auto Test Cases\1_Tests\test_0SmokeTest.py"
~~~

### Run one functional test

Run the desired command from the project root:

~~~powershell
# Test 01 — Search bar
.\.venv\Scripts\python.exe -m pytest "2-Auto Test Cases\1_Tests\test_AllGames_01_SearchBar.py"

# Test 02 — Personalized filters
.\.venv\Scripts\python.exe -m pytest "2-Auto Test Cases\1_Tests\test_AllGames_04_PersonalizedFilters.py"

# Test 03 — Cookie settings
.\.venv\Scripts\python.exe -m pytest "2-Auto Test Cases\1_Tests\test_Discover_02_CookieSettings.py"

# Test 04 — Essential cart functions
.\.venv\Scripts\python.exe -m pytest "2-Auto Test Cases\1_Tests\test_YourCart_01_EssentialCartFunctions.py"

# Test 05 — Saving cart
.\.venv\Scripts\python.exe -m pytest "2-Auto Test Cases\1_Tests\test_YourCart_02_SavingCart.py"
~~~

### Run the complete pack of tests

This runs the smoke tests and all five functional test files:

~~~powershell
.\.venv\Scripts\python.exe -m pytest
~~~

Pytest runs tests sequentially by default. Do not run tests in parallel or repeatedly against the live store.

## Test coverage

| App button | Scenario |
| --- | --- |
| Test 01 | Search for games |
| Test 02 | Personalized filters |
| Test 03 | Cookie settings |
| Test 04 | Essential cart functions |
| Test 05 | Cart persistence |

The Smoke Test checks the project runtime and that Playwright can start. Functional tests cover store browsing, search and filters, cookie settings, cart operations, and cart persistence.

## Requirements and scope

- Windows
- Internet access during setup and when running tests
- Python 3.10 or newer; setup can install Python 3.12 through winget if needed
- The store is a live site. These tests do not create an account, enter payment details, or complete a purchase.
