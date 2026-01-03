import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, TypedDict

import requests
from bs4 import BeautifulSoup, Tag
from requests import Response, Session

# Network debug
# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://licenseportal.it.chula.ac.th"
URL_LOGIN = f"{BASE_URL}/"
URL_BORROW = f"{BASE_URL}/Home/Borrow"


class LicenseConfig(TypedDict):
    id: str
    days: int


LICENSES: Dict[str, LicenseConfig] = {
    "adobe": {"id": "5", "days": 7},
    "foxit": {"id": "7", "days": 90},
    "zoom": {"id": "2", "days": 120},
}


class PortalClient:
    def __init__(self, email: str, password: str) -> None:
        self.email: str = email
        self.password: str = password
        self.session: Session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.session.verify = False

    def _get_form_payload(
        self, html: str, form_action: Optional[str] = None
    ) -> Dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        payload: Dict[str, str] = {}

        container: Any = soup
        if form_action:
            found_form = soup.find("form", action=form_action)
            if found_form:
                container = found_form

        for inp in container.find_all("input"):
            if isinstance(inp, Tag):
                name = inp.get("name")
                value = inp.get("value", "")

                if isinstance(name, str):
                    if isinstance(value, str):
                        payload[name] = value
                    elif value is None:
                        payload[name] = ""
                    else:
                        payload[name] = str(value)

        for sel in container.find_all("select"):
            if isinstance(sel, Tag):
                name = sel.get("name")

                if isinstance(name, str):
                    selected = sel.find("option", selected=True)
                    if isinstance(selected, Tag):
                        val = selected.get("value", "")
                        payload[name] = str(val) if val is not None else ""
                    else:
                        payload[name] = ""

        return payload

    def login(self) -> None:
        logging.info("Logging in...")
        resp: Response = self.session.get(URL_LOGIN)
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

        post: Response = self.session.post(URL_LOGIN, data=payload)

        if "UserName" in post.text and "Password" in post.text:
            raise PermissionError("Login failed. Check credentials.")

    def borrow(self, license_key: str) -> bool:
        if license_key not in LICENSES:
            logging.error(f"Unknown license key: {license_key}")
            return False

        config = LICENSES[license_key]
        days = config["days"]
        license_id = config["id"]

        logging.info(f"Borrowing: {license_key} (Duration: {days} days)")

        resp: Response = self.session.get(URL_BORROW)
        resp.raise_for_status()

        payload = self._get_form_payload(resp.text, form_action="/Home/Borrow")

        if "__RequestVerificationToken" not in payload:
            logging.error("CSRF token missing on borrow page")
            return False

        now = datetime.now()
        payload.update(
            {
                "ProgramLicenseID": license_id,
                "BorrowDateStr": now.strftime("%d/%m/%Y"),
                "ExpiryDateStr": (now + timedelta(days=days)).strftime("%d/%m/%Y"),
            }
        )

        post: Response = self.session.post(URL_BORROW, data=payload)

        if post.history and post.history[0].status_code == 302:
            return True

        if "The field UserPrincipalName is required" in post.text:
            logging.error("Server rejected payload (Missing UserPrincipalName)")
        else:
            logging.error(f"Borrow failed. Status: {post.status_code}")

        return False
