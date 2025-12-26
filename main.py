import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================== НАСТРОЙКИ ==================

BASE_URL = "https://search-sofia-adms-g.justice.bg/Acts/Actsindex"
PAGES_TO_CRAWL = 3              # сложи 3 за ~150 решения
DOWNLOAD_DIR = "Data"
CHROMEDRIVER_PATH = (
    r"C:\Users\dimit\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
)

# ===============================================

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- Chrome options ----------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")

# ---------- Chrome driver ----------
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)


download_dir = os.path.abspath(DOWNLOAD_DIR)

prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}

options.add_experimental_option("prefs", prefs)

def download_file(url: str, index: int):
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    cd = r.headers.get("Content-Disposition", "")
    if "filename=" in cd:
        base_name = cd.split("filename=")[-1].strip('"; ')
    else:
        base_name = url.split("/")[-1]

    name, ext = os.path.splitext(base_name)
    filename = f"{name}_{index}{ext}"

    path = os.path.join(DOWNLOAD_DIR, filename)

    print("⬇ Изтеглям:", filename)
    with open(path, "wb") as f:
        f.write(r.content)


try:
    # 1️⃣ Отваряме директно iframe страницата
    driver.get(BASE_URL)

    for page in range(1, PAGES_TO_CRAWL + 1):
        print(f"\n📄 Страница {page}")

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(normalize-space(.), 'Решение')]")
            )
        )

        # 1️⃣ СЪБИРАМЕ URL-ИТЕ (без да навигираме!)
        download_urls = [
            link.get_attribute("href")
            for link in driver.find_elements(
                By.XPATH,
                "//a[contains(normalize-space(.), 'Решение')]"
            )
            if link.get_attribute("href")
        ]

        print(f"Намерени линкове: {len(download_urls)}")

        # 2️⃣ СВАЛЯМЕ ГИ С REQUESTS
        counter = 0
        # TODO: fix the problem with counter for the different pages
        for url in download_urls:
            download_file(url,counter)
            counter+=1

        # 3️⃣ NEXT PAGE
        if page < PAGES_TO_CRAWL:
            next_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//li[contains(@class,'PagedList-skipToNext')]/a")
                )
            )

            next_button.click()

finally:
    driver.quit()

print("\n✅ Готово – решенията са изтеглени успешно.")
