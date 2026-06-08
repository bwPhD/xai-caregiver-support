#!/usr/bin/env python3
"""Wake a Streamlit Community Cloud app from GitHub Actions."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "wake_up.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("wake-streamlit")

WAKE_BUTTON_TEXT = (
    "get this app back up",
    "wake it back up",
    "wake this app",
)
SLEEP_TEXT = (
    "gone to sleep",
    "due to inactivity",
    "get this app back up",
)


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("STREAMLIT_URL is empty")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def ping(url: str) -> None:
    try:
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "github-actions-streamlit-wake/1.0"},
        )
        logger.info("HTTP ping returned status %s", response.status_code)
    except requests.RequestException as exc:
        logger.warning("HTTP ping failed: %s", exc)


def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)
    return driver


def find_wake_button(driver: webdriver.Chrome):
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for button in buttons:
        text = " ".join(button.text.lower().split())
        if any(needle in text for needle in WAKE_BUTTON_TEXT):
            return button
    return None


def page_looks_awake(driver: webdriver.Chrome) -> bool:
    page_text = " ".join(driver.page_source.lower().split())
    if any(needle in page_text for needle in SLEEP_TEXT):
        return False

    app_selectors = (
        '[data-testid="stApp"]',
        '[data-testid="stSidebar"]',
        ".stApp",
        "main",
    )
    return any(driver.find_elements(By.CSS_SELECTOR, selector) for selector in app_selectors)


def wake_with_browser(url: str) -> bool:
    driver = create_driver()
    try:
        logger.info("Opening %s", url)
        driver.get(url)
        WebDriverWait(driver, 45).until(
            lambda current_driver: current_driver.execute_script(
                "return document.readyState"
            )
            == "complete"
        )
        time.sleep(5)

        button = find_wake_button(driver)
        if button is not None:
            logger.info("Sleep page detected; clicking wake button")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            button.click()

            WebDriverWait(driver, 180).until(
                lambda current_driver: page_looks_awake(current_driver)
            )
            logger.info("App appears awake after button click")
            return True

        if page_looks_awake(driver):
            logger.info("App is already awake")
            return True

        logger.warning("Could not confirm app state. Title: %s", driver.title)
        return False
    finally:
        driver.quit()


def wake_with_retries(url: str, max_attempts: int = 3) -> int:
    for attempt in range(1, max_attempts + 1):
        logger.info("Wake attempt %s/%s", attempt, max_attempts)
        ping(url)

        try:
            if wake_with_browser(url):
                logger.info("Wake-up completed successfully")
                return 0
        except (TimeoutException, WebDriverException, RuntimeError) as exc:
            logger.warning("Wake attempt failed: %s", exc)

        if attempt < max_attempts:
            wait_seconds = attempt * 30
            logger.info("Waiting %s seconds before retry", wait_seconds)
            time.sleep(wait_seconds)

    logger.error("Wake-up failed after %s attempts", max_attempts)
    return 1


def main() -> int:
    raw_url = os.getenv("STREAMLIT_URL", "")
    try:
        url = normalize_url(raw_url)
    except ValueError as exc:
        logger.error("%s. Add this repository secret in GitHub Actions.", exc)
        return 1

    return wake_with_retries(url)


if __name__ == "__main__":
    raise SystemExit(main())
