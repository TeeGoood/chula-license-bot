from playwright.sync_api import Playwright, sync_playwright, expect
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

url = "https://licenseportal.it.chula.ac.th"
email = os.getenv("LOGIN_EMAIL")
password = os.getenv("LOGIN_PASSWORD")

start = datetime.now()
end = start + timedelta(days=7)
options = {
  "adobe": "5",
  "foxit": "7",
  "zoom": "2",
}

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # login
    page.goto(url)
    page.locator("#UserName").fill(email)
    page.locator("#Password").fill(password)
    page.locator("button[type='submit']").click()

    # borrow license
    page.goto(f"{url}/Home/Borrow")
    page.locator("#ProgramLicenseID").select_option(options["foxit"])
    page.locator("#BorrowDateStr").fill(start.strftime("%d/%m/%Y"))
    page.keyboard.press("Escape")
    page.locator("#ExpiryDateStr").fill(end.strftime("%d/%m/%Y"))
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Save").click()

    context.close()
    browser.close()
