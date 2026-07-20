import os
import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


@pytest.fixture(scope="function")
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    drv = webdriver.Chrome(options=options)
    drv.set_page_load_timeout(60)
    yield drv
    drv.quit()


def _save_screenshot(drv, name):
    try:
        path = os.path.join(os.getcwd(), name)
        drv.save_screenshot(path)
        print(f"Screenshot saved to: {path}")
    except Exception as exc:
        print(f"Failed to save screenshot: {exc}")


def test_navigate_to_youtube_movies_section(driver):
    wait = WebDriverWait(driver, 30)
    try:
        # Step 1: Navigate to YouTube homepage
        driver.get("https://www.youtube.com/")
        wait.until(EC.title_contains("YouTube"))
        assert "youtube.com" in driver.current_url.lower(), \
            f"Expected youtube.com in URL, got {driver.current_url}"

        # Give the SPA a moment to hydrate the side/guide nav
        time.sleep(2)

        # Step 2: Click the 'Movies' entry in the guide/side nav.
        # Prefer aria-label / text based match against a tp-yt-paper-item.
        movies_locators = [
            (By.XPATH, "//tp-yt-paper-item[.//yt-formatted-string[normalize-space(text())='Movies']]"),
            (By.XPATH, "//a[@title='Movies']"),
            (By.XPATH, "//ytd-guide-entry-renderer[.//yt-formatted-string[normalize-space(text())='Movies']]"),
            (By.XPATH, "//*[normalize-space(text())='Movies']"),
        ]

        movies_element = None
        last_err = None
        for by, sel in movies_locators:
            try:
                movies_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((by, sel))
                )
                break
            except TimeoutException as e:
                last_err = e
                continue

        if movies_element is None:
            raise TimeoutException(
                f"Could not locate the 'Movies' navigation entry. Last error: {last_err}"
            )

        try:
            movies_element.click()
        except WebDriverException:
            driver.execute_script("arguments[0].click();", movies_element)

        # Step 3: Assert we landed on the Movies storefront
        wait.until(EC.title_contains("Movies"))
        wait.until(lambda d: "/feed/storefront" in d.current_url or "movies" in d.current_url.lower())

        assert "Movies" in driver.title, f"Expected 'Movies' in title, got {driver.title!r}"
        assert "/feed/storefront" in driver.current_url or "movies" in driver.current_url.lower(), \
            f"Unexpected URL after clicking Movies: {driver.current_url}"

    except Exception as exc:
        _save_screenshot(driver, "navigate_to_youtube_movies_section_failure.png")
        raise
