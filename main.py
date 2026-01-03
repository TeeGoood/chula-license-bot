import logging
import os
import pickle
import sys
import textwrap
from datetime import datetime, timedelta

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright


def main():
    load_dotenv()
    setup_logger()

    url = "https://licenseportal.it.chula.ac.th"
    email = os.getenv("LOGIN_EMAIL") or ""
    password = os.getenv("LOGIN_PASSWORD") or ""

    select_options = {
        "adobe": "5",
        "foxit": "7",
        "zoom": "2",
    }

    now = datetime.now()
    start = now
    end = start + timedelta(days=7)

    licenses = get_licenses()
    last_borrowed = get_last_borrowed()

    with sync_playwright() as playwright:
        # setup
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # login
        page.goto(url)
        page.locator("#UserName").fill(email)
        page.locator("#Password").fill(password)
        page.locator("button[type='submit']").click()

        # borrow licenses
        for license in licenses:
            # check borrow period
            if now - last_borrowed[license] < timedelta(days=6):
                logging.info(
                    f"{license} don't reach borrow period, will be borrowed in {6 - (now - last_borrowed[license]).days} days"
                )
                continue

            page.goto(f"{url}/Home/Borrow")
            page.locator("#ProgramLicenseID").select_option(select_options[license])
            page.locator("#BorrowDateStr").fill(start.strftime("%d/%m/%Y"))
            page.keyboard.press("Escape")
            page.locator("#ExpiryDateStr").fill(end.strftime("%d/%m/%Y"))
            page.keyboard.press("Escape")
            page.get_by_role("button", name="Save").click()

            last_borrowed[license] = now
            logging.info(f"Borrow {license} success")

        pickle.dump(last_borrowed, open("last_borrowed.pickle", "wb"))


def setup_logger():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
    )


def get_licenses():
    if len(sys.argv) < 2:
        print(
            textwrap.dedent("""
        Usage: python main.py <license> [<license> ...]

        License:
          foxit | zoom | adobe

        Example:
          python main.py foxit zoom
      """)
        )
        exit(1)

    return sys.argv[1:]


def get_last_borrowed():
    try:
        with open("last_borrowed.pickle", "rb") as f:
            last_borrowed = pickle.load(f)
    except FileNotFoundError:
        epoch = datetime.fromtimestamp(0)
        last_borrowed = {
            "adobe": epoch,
            "foxit": epoch,
            "zoom": epoch,
        }
    return last_borrowed


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Borrow failed")
