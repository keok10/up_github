from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
import time

def find_element_or_empty_text(element, css_selector):
    try:
        return element.find_element(By.CSS_SELECTOR, css_selector).text
    except NoSuchElementException:
        return ""

chrome_options = Options()
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_driver_path = "/usr/local/bin/chromedriver"
driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
driver.set_page_load_timeout(150)

wait = WebDriverWait(driver, 20)  # 最大で20秒待機

with open('data_shimokita.csv', mode='a', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    total_processed = 0
    MAX_RETRIES = 4

    for page_num in range(13, 41):
        url = f'.com/tokyo/rstLst/{page_num}/'
        for attempt in range(MAX_RETRIES):
            try:
                driver.get(url)
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list-rst')))
                break
            except TimeoutException:
                if attempt < MAX_RETRIES - 1:
                    print(f"Timeout occurred. Retrying... ({attempt + 1}/{MAX_RETRIES})")
                    continue
                else:
                    print("Failed to load the page after several attempts. Skipping...")
                    break

        restaurants = driver.find_elements(By.CSS_SELECTOR, '.list-rst')
        restaurant_links = [rest.find_element(By.CSS_SELECTOR, '.list-rst__rst-name a').get_attribute("href") for rest in restaurants if rest]

        for link in restaurant_links:
            for attempt in range(MAX_RETRIES):
                try:
                    driver.get(link)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.display-name')))
                    break
                except TimeoutException:
                    if attempt < MAX_RETRIES - 1:
                        print(f"Timeout occurred while accessing {link}. Retrying... ({attempt + 1}/{MAX_RETRIES})")
                        continue
                    else:
                        print(f"Failed to load detail page {link} after several attempts. Skipping...")
                        break

            name = find_element_or_empty_text(driver, '.display-name')
            evaluation = find_element_or_empty_text(driver, '.rdheader-rating__score-val-dtl')
            homepage = find_element_or_empty_text(driver, '.homepage a')
            toiawase_number = find_element_or_empty_text(driver, '.rstinfo-table__tel-num')
            tabelog_url = driver.current_url

            csv_writer.writerow([name, evaluation, homepage, toiawase_number, tabelog_url])

            total_processed += 1
            print(f"合計で {total_processed} 件のレストランを処理しました。")

            time.sleep(7)  # この待機時間は必要に応じて調整してください

driver.quit()
