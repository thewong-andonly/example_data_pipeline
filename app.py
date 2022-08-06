import time
import json
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from classes.Webscrapers import Webscraper, DynamicPageScraper
import logging
import traceback

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s. %(levelname)s: %(message)s",
)


def main():
    json_file_name = "all_data.json"
    url = ""  # blank
    project = DynamicPageScraper(Webscraper)
    project.navigate_url(url)
    target_rows = 100

    start_time = time.time()
    try:
        while True:
            project.visbility_of_all_elements_implicit_wait(
                By.ID, "pageSizeSelectsearchSignalsData"
            )
            dropdown = Select(
                project.driver.find_element(By.ID, "pageSizeSelectsearchSignalsData")
            )
            dropdown.select_by_value(str(target_rows))
            time.sleep(3)
            row_count = len(project.driver.find_elements(By.TAG_NAME, "tr"))
            logging.info(f"Row count: {row_count}.")
            if row_count >= target_rows:
                break
            else:
                logging.info("Row count too low.  Retrying to set rows.")
                project.driver.refresh()
        page_count = int(
            project.driver.find_element(By.CLASS_NAME, "pagination-panel-total").text
        )
        project.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception as e:
        logging.warning(
            f"Error setting row count. Exception {e}.  Stack trace: {traceback.print_exc()}"
        )
    try:
        all_data = []
        logging.info(f"Getting data for {page_count} pages.")
        for page in range(1, page_count + 1):
            logging.info(f"Parsing page {page} of {page_count}.")

            rows = project.get_table_data(tag="tr")
            rows_as_text = [row.text for row in rows]
            row_names = [row for row in rows_as_text[0].split()]

            table_data = project.get_table_data(tag="td")
            table_data_as_text = [item.text for item in table_data]

            a_tags = project.driver.find_elements(By.TAG_NAME, "a")
            hyperlinks = [link.get_attribute("href") for link in a_tags]
            hyperlinks = [link for link in hyperlinks if link and "analysis" in link]
            hyperlinks = {num: link for num, link in enumerate(hyperlinks)}

            table_dicts = []
            data_dict = {}
            i = 0
            hyperlink_counter = 0
            reset_point = len(row_names) - 1
            for text_row in table_data_as_text:
                if i == reset_point:
                    i = 0
                    table_dicts.append(data_dict)
                    data_dict = {}
                else:
                    data_dict[row_names[i]] = text_row
                    i += 1
                    hyperlink_counter += 1

            for i, record in enumerate(table_dicts):
                record["hyperlink"] = hyperlinks[i]

            for record in table_dicts:
                all_data.append(record)

            if page == page_count:
                logging.info(f"All pages completed. Total records: {len(all_data)}")
                break

            if page > 0:
                logging.info(f"Moving to page {page+1}.")
                project.element_to_be_clickable_implicit_wait(
                    By.XPATH, tag="//a[@class='btn btn-sm default next ']"
                )
                button = project.driver.find_element(
                    By.XPATH, "//a[@class='btn btn-sm default next ']"
                )
                button.click()
                time.sleep(2)
            logging.info(f"Page {page} parsed.")
        project.driver.quit()
        with open(json_file_name, "w") as save_file:
            json.dump(all_data, save_file)
        logging.info("Main page data saved.")
    except Exception as e:
        logging.warning(
            f"Error scraping main page. Exception: {e}. Stack trace: {traceback.print_exc()}"
        )
    try:
        logging.info("Scraping hyperlink data.")
        with open(json_file_name) as json_file:
            all_data = json.load(json_file)
        navigator = DynamicPageScraper(Webscraper)
        for record_number, record in enumerate(all_data):
            url = record["hyperlink"]
            navigator.navigate_url(url)
            sub_header_data = [
                item.text.split(",")
                for item in navigator.driver.find_elements(
                    By.XPATH,
                    "//div[@class='caption-helper font-blue-sharp bold master-description-container']",
                )
                if item.text
            ]
            description = navigator.driver.find_element(By.TAG_NAME, "p").text
            banner_data = [
                item.text.split("\n")[::-1]
                for item in navigator.driver.find_elements(By.CLASS_NAME, "details")
            ]
            inner_table_data = [
                item.text.split("\n")
                for item in navigator.driver.find_elements(
                    By.CLASS_NAME, "list-group-item"
                )
            ]
            for item in banner_data:
                inner_table_data.append(item)
            inner_page_dict = {item[0]: item[1] for item in inner_table_data}
            for num, item in enumerate(sub_header_data[0], start=1):
                inner_page_dict[f"sub_header_{num}"] = item

            inner_page_dict["description"] = description
            for key, value in inner_page_dict.items():
                record[key] = value
            logging.info(f"Record {record_number} of {len(all_data)} parsed.")
        with open(json_file_name, "w") as save_file:
            json.dump(all_data, save_file)
        logging.info("Finish scraping hyperlink data.")
    except Exception as e:
        logging.warn(f"Error processing record {record}.")
        logging.warning(f"Error scraping hyperlinks. Exception {e}")
    try:
        logging.info("Processing data.")
        with open(json_file_name) as json_file:
            all_data = json.load(json_file)
        df = pd.DataFrame.from_dict(all_data)
        columns_reformatted = {
            col: col.lower().strip().replace(":", "") for col in df.columns
        }
        df.rename(columns=columns_reformatted, inplace=True)
        columns_renamed = {
            "sub_header_3": "currency",
            "sub_header_4": "platform",
            "sub_header_5": "ratio",
            "sub_header_6": "platform_2",
        }
        df.rename(columns=columns_renamed, inplace=True)
        df.dropna(how="all", axis=1, inplace=True)
        df["description"] = df["description"].str.replace(r"\s+", " ", regex=True)
        df.to_csv("forex_signal_data.csv", index=False)
        logging.info("Data processed.")
        logging.info(f"Finished in {(time.time() - start_time)/60:.2f} minutes.")
    except Exception as e:
        logging.warning(
            f"Error processing data as dataframe. Exception {e}.  Stack trace: {traceback.print_exc()}"
        )


if __name__ == "__main__":
    main()
