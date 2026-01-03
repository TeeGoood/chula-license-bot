import os
import pickle
from datetime import datetime, timedelta

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

url = "https://licenseportal.it.chula.ac.th"
email = os.getenv("LOGIN_EMAIL") or ""
password = os.getenv("LOGIN_PASSWORD") or ""
options = {
    "adobe": "5",
    "foxit": "7",
    "zoom": "2",
}
option = "foxit"
now = datetime.now()
start = now
end = start + timedelta(days=7)


def main():
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

    if now - last_borrowed[option] < timedelta(days=6):
        print(f"Don't reach borrow period, {(now - last_borrowed[option]).days} days")
        return

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # login
            page.goto(url)
            page.locator("#UserName").fill(email)
            page.locator("#Password").fill(password)
            page.locator("button[type='submit']").click()

            # borrow license
            page.goto(f"{url}/Home/Borrow")
            page.locator("#ProgramLicenseID").select_option(options[option])
            page.locator("#BorrowDateStr").fill(start.strftime("%d/%m/%Y"))
            page.keyboard.press("Escape")
            page.locator("#ExpiryDateStr").fill(end.strftime("%d/%m/%Y"))
            page.keyboard.press("Escape")
            page.get_by_role("button", name="Save").click()

            context.close()
            browser.close()

            last_borrowed[option] = now
            pickle.dump(last_borrowed, open("last_borrowed.pickle", "wb"))

            print(f"borrow success at {now.strftime('%d/%m/%Y, %H:%M:%S')}")
    except Exception as e:
        print(f"borrow failed at {now.strftime('%d/%m/%Y, %H:%M:%S')}: {e}")


if __name__ == "__main__":
    main()
