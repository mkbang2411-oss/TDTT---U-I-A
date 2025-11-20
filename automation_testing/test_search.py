# test_search.py
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.fixture()
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
    driver.get("http://127.0.0.1:5000/")

    yield driver
    driver.quit()


def test_search_food(driver):

    time.sleep(1)

    # Nhập từ khóa
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "query"))
    )
    search_box.send_keys("Lẩu")

    time.sleep(1)

    driver.find_element(By.ID, "btnSearch").click()

    # ❗ Không chờ sidebar nữa — vì search không mở sidebar

    # Chờ markers xuất hiện trên map
    markers = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".leaflet-marker-icon")
        )
    )

    # Đảm bảo có ít nhất 1 marker sau khi search
    assert len(markers) > 0, "Search 'Lẩu' nhưng không hiện marker nào!"

    time.sleep(2)  # để bạn nhìn rõ browser trước khi đóng
