import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

# Network debug
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://licenseportal.it.chula.ac.th"
URL_LOGIN = f"{BASE_URL}/"
URL_BORROW = f"{BASE_URL}/Home/Borrow"

LICENSE_IDS = {
    "adobe": "5",
    "foxit": "7",
    "zoom": "2",
}


class PortalClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.session.verify = False

    def _get_form_payload(self, html, form_action=None):
        soup = BeautifulSoup(html, "html.parser")
        payload = {}

        container = soup.find("form", action=form_action) or soup

        for inp in container.find_all("input"):
            if inp.get("name"):
                payload[inp.get("name")] = inp.get("value", "")

        for sel in container.find_all("select"):
            if sel.get("name"):
                selected = sel.find("option", selected=True)
                payload[sel.get("name")] = selected["value"] if selected else ""

        return payload

    def login(self):
        logging.info("Logging in...")
        resp = self.session.get(URL_LOGIN)
        resp.raise_for_status()

        payload = self._get_form_payload(resp.text)
        if "__RequestVerificationToken" not in payload:
            raise ValueError("CSRF token missing from login page")

        payload.update(
            {
                "UserName": self.email,
                "Password": self.password,
                "LanguageCode": "Thai",
            }
        )

        post = self.session.post(URL_LOGIN, data=payload)

        if "UserName" in post.text and "Password" in post.text:
            raise PermissionError("Login failed. Check credentials.")

    def borrow(self, license_key):
        if license_key not in LICENSE_IDS:
            logging.error(f"Unknown license key: {license_key}")
            return False

        logging.info(f"Borrowing: {license_key}")
        resp = self.session.get(URL_BORROW)
        resp.raise_for_status()

        payload = self._get_form_payload(resp.text, form_action="/Home/Borrow")

        if "__RequestVerificationToken" not in payload:
            logging.error("CSRF token missing on borrow page")
            return False

        now = datetime.now()
        payload.update(
            {
                "ProgramLicenseID": LICENSE_IDS[license_key],
                "BorrowDateStr": now.strftime("%d/%m/%Y"),
                "ExpiryDateStr": (now + timedelta(days=7)).strftime("%d/%m/%Y"),
            }
        )

        post = self.session.post(URL_BORROW, data=payload)

        if post.history and post.history[0].status_code == 302:
            return True

        if "The field UserPrincipalName is required" in post.text:
            logging.error("Server rejected payload (Missing UserPrincipalName)")
        else:
            logging.error(f"Borrow failed. Status: {post.status_code}")

        return False
