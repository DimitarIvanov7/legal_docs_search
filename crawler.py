import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://search-sofia-adms-g.justice.bg/Acts/ActsIndex?page=200"
PAGES_TO_CRAWL = 5
DOWNLOAD_DIR = "Data/Documents_Eval"
CHROMEDRIVER_PATH = (
    r"C:\Users\dimit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

download_dir = os.path.abspath(DOWNLOAD_DIR)

session = requests.Session()

# Retry стратегия
retries = Retry(
    total=5,
    backoff_factor=1.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://search-sofia-adms-g.justice.bg/Acts/Actsindex"
}

def download_file(url: str, index: int):
    try:
        r = session.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()

        cd = r.headers.get("Content-Disposition", "")
        if "filename=" in cd:
            base_name = cd.split("filename=")[-1].strip('"; ')
        else:
            base_name = f"reshenie_{index}.bin"

        name, ext = os.path.splitext(base_name)
        filename = f"{name}_{index}{ext}"

        path = os.path.join(DOWNLOAD_DIR, filename)

        print("Изтегляне:", filename)
        with open(path, "wb") as f:
            f.write(r.content)

        time.sleep(1.5)

    except requests.exceptions.RequestException as e:
        print(f" Пропуснат файл {index}: {e}")

counter = 0
try:
    driver.get(BASE_URL)

    for page in range(1, PAGES_TO_CRAWL + 1):
        print(f"\n Страница {page}")

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(normalize-space(.), 'Решение')]")
            )
        )

        download_urls = [
            link.get_attribute("href")
            for link in driver.find_elements(
                By.XPATH,
                "//a[contains(normalize-space(.), 'Решение')]"
            )
            if link.get_attribute("href")
        ]

        print(f"Намерени линкове: {len(download_urls)}")


        for url in download_urls:
            if type(url) == str:
                download_file(url,counter)
                counter+=1

        if page < PAGES_TO_CRAWL:
            next_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//li[contains(@class,'PagedList-skipToNext')]/a")
                )
            )

            next_button.click()

finally:
    driver.quit()

print("\n Решенията са изтеглени успешно.")
