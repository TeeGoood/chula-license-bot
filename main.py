import argparse
import logging
import os
import pickle
import sys
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv

from client import LICENSE_IDS, PortalClient

STATE_FILE = "last_borrowed.pickle"


def load_state() -> Dict[str, datetime]:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "rb") as f:
        data: Any = pickle.load(f)
        if isinstance(data, dict):
            return data
        return {}


def save_state(data: Dict[str, datetime]) -> None:
    with open(STATE_FILE, "wb") as f:
        pickle.dump(data, f)


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("licenses", nargs="+", choices=list(LICENSE_IDS.keys()))
    args = parser.parse_args()

    email: str | None = os.getenv("LOGIN_EMAIL")
    password: str | None = os.getenv("LOGIN_PASSWORD")

    if not email or not password:
        logging.critical("Environment variables LOGIN_EMAIL or LOGIN_PASSWORD missing.")
        sys.exit(1)

    state: Dict[str, datetime] = load_state()
    client = PortalClient(email, password)

    try:
        client.login()

        now = datetime.now()

        for item in args.licenses:
            last_date: datetime | None = state.get(item)

            if last_date and (now - last_date).days < 6:
                logging.info(
                    f"Skipping {item}: Already active ({(now - last_date).days} days old)."
                )
                continue

            if client.borrow(item):
                logging.info(f"Successfully borrowed {item}")
                state[item] = now

        save_state(state)

    except Exception as e:
        logging.exception(f"Runtime error: {e}")


if __name__ == "__main__":
    main()
