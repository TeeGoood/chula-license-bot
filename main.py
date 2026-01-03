import os
import pickle
import sys
import textwrap
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
    if len(sys.argv) < 2:
        print(
            textwrap.dedent("""
          Usage: python main.py <application> [<application> ...]

          Applications:
            foxit | zoom | adobe

          Example:
            python main.py foxit zoom adobe
        """)
        )
        return

    programs = sys.argv[1:]

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
            for program in programs:
                if now - last_borrowed[program] < timedelta(days=6):
                    print(
                        f"{program} don't reach borrow period, {(now - last_borrowed[option]).days} days"
                    )
                    continue

                page.goto(f"{url}/Home/Borrow")
                page.locator("#ProgramLicenseID").select_option(options[program])
                page.locator("#BorrowDateStr").fill(start.strftime("%d/%m/%Y"))
                page.keyboard.press("Escape")
                page.locator("#ExpiryDateStr").fill(end.strftime("%d/%m/%Y"))
                page.keyboard.press("Escape")
                page.get_by_role("button", name="Save").click()

                last_borrowed[program] = now

            context.close()
            browser.close()
            pickle.dump(last_borrowed, open("last_borrowed.pickle", "wb"))
            print(
                f"borrow {', '.join(programs)} success at {now.strftime('%d/%m/%Y, %H:%M:%S')}"
            )
    except Exception as e:
        print(f"borrow failed at {now.strftime('%d/%m/%Y, %H:%M:%S')}: {e}")


if __name__ == "__main__":
    main()
