from bs4 import BeautifulSoup, Comment
from openpyxl import load_workbook
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def extract_playerstats(driver,url, file_path):
    save_tbody_html(driver,url, file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("tbody")

    rows_data = []

    for row in table.find_all("tr"):
        if "class" in row.attrs and "thead" in row["class"]:
            continue

        row_dict = {}
        for cell in row.find_all(["th", "td"]):
            key = cell.get("data-stat")
            if key:
                row_dict[key] = cell.get_text(strip=True)

        if row_dict:
            rows_data.append(row_dict)

    return rows_data

def save_tbody_html(driver,url,file_path):


    driver.get(url)

    wait = WebDriverWait(driver, 30)
    tbody = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#stats_standard_20 tbody")))
    tbody_html = tbody.get_attribute("outerHTML")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(tbody_html)





