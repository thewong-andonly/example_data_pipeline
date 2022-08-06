# Build in libs
from abc import ABC
from dataclasses import dataclass

# Third party Libs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


class Webscraper(ABC):
    pass


@dataclass
class DynamicPageScraper(Webscraper):
    url: str

    def __post_init__(self):
        self.options = Options()
        self.options.headless = True
        self.driver = webdriver.Firefox(
            executable_path="geckodriver.exe", options=self.options
        )

    def navigate_url(self, url, maximise=False):
        if maximise:
            self.driver.maximize_window()
        try:
            self.driver.get(url)
        except Exception as e:
            print(f"Problem with {__name__}. Exception: {e}.")

    def get_table_data(self, tag=["tr", "td"]):
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, tag))
        )
        try:
            data = self.driver.find_elements(By.TAG_NAME, tag)
            return [item for item in data]
        except Exception as e:
            print(f"Problem with {__name__}. Exception: {e}.")

    def visbility_of_all_elements_implicit_wait(self, by_method: By, tag: str, time=20):
        print(f"Waiting for all {tag} tags to be visible...")
        WebDriverWait(self.driver, time).until(
            EC.visibility_of_all_elements_located((by_method, tag))
        )
        print(f"All {tag} visible.")

    def element_to_be_clickable_implicit_wait(self, by_method: By, tag: str, time=20):
        print(f"Waiting for {tag} to be clickable...")
        WebDriverWait(self.driver, time).until(
            EC.element_to_be_clickable((by_method, tag))
        )
        print(f"{tag} clickable.")
