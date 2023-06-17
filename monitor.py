
import base64
import datetime
import io
import random
import sys
from time import sleep

import requests
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

SUCCESS = "Окно"
NO_LUCK = "Извините, но в настоящий момент на интересующее Вас"


def read_config(config):
    with open(config, 'r') as file:
        data = yaml.safe_load(file)
        return data

def parse_image(image, config):
    payload = {
        "folderId": config["folder_id"],
        "analyze_specs": [
            {
                "content": image,
                "features": [
                    {
                        "type": "TEXT_DETECTION",
                        "text_detection_config": {
                            "language_codes": ["en"]
                        }
                    }
                ]
            }
        ]
    }
    headers = {"Authorization": f"Api-Key {config['api_key']}"}
    response = requests.post(
        "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze",
        headers=headers,
        json=payload
    )
    if response.status_code == 200:
        # Extract recognized text from the API response
        response_data = response.json()
        try:
            text = response_data["results"][0]["results"][0]["textDetection"]["pages"][0]["blocks"][0]["lines"][0]["words"][0]["text"]
        except KeyError:
            print(f"Can't parse text response_data: {response_data}")
            raise
        return text
    print("Error:", response.status_code, response.text)
    raise KeyError

def crawl_url(url, config):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome('chromedriver', options=chrome_options)
    browser.get(url)
    img = browser.find_element(By.ID, "ctl00_MainContent_imgSecNum")
    try:
        number = parse_image(img.screenshot_as_base64, config["YC"])
    except Exception:
        print("FAILED")
        raise
    field = browser.find_element(By.ID, "ctl00_MainContent_txtCode")
    field.clear()
    field.send_keys(number)
    field.send_keys(Keys.ENTER)
    confirm_button = browser.find_element(By.ID, "ctl00_MainContent_ButtonB")
    confirm_button.send_keys(Keys.ENTER)
    central_pannel = browser.find_element(By.ID, "center-panel")
    if SUCCESS in central_pannel.text:
        print("SUCCESS")
        send_base64_image(
            central_pannel.screenshot_as_base64,
            "Есть доступное окно",
            config["telegram"]["chat_id"],
            config["telegram"]["token"]
            )
    elif NO_LUCK in central_pannel.text:
        print("no luck")
        return None
    else:
        print("error")
        send_base64_image(
            central_pannel.screenshot_as_base64,
            "can't recognise result",
            config["telegram"]["chat_id"],
            config["telegram"]["token"]
            )
        return None

def send_base64_image(base64_image, text_to_send, destination_id, token):
    send_text_url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': destination_id,
        'text': text_to_send
    }
    result = requests.post(send_text_url, data=payload)
    if result.status_code == 200:
        print("text send successfully")
    else:
        print(f"Failed to send text: {result.status_code}, {result.text}")
    if not base64_image:
        return
    image_data = base64.b64decode(base64_image)
    image_file = io.BytesIO(image_data)

    files = {'photo': ('image.jpg', image_file, 'image/jpeg')}
    data = {'chat_id': destination_id}
    send_photo_url = f'https://api.telegram.org/bot{token}/sendPhoto'
    result = requests.post(send_photo_url, data=data, files=files)

    if result.status_code == 200:
        print("Image sent successfully")
    else:
        print(f"Failed to send image: {result.status_code} {result.text}")

def main():
    config = read_config('config.yaml')
    if datetime.datetime.now().hour < 6:
        sys.exit()
    if config.get("sleep"):
        minutes_to_sleep = random.randint(1, 55)
        sec_to_sleep = random.randint(1, 55)
        print(datetime.datetime.now())
        print(f"going to sleep {minutes_to_sleep} minutes {sec_to_sleep} sec")
        sleep(minutes_to_sleep * 60 + sec_to_sleep)
    try:
        crawl_url(config["URLS_TO_CHECK"][0], config)
    except Exception:
        if len(config["URLS_TO_CHECK"]) > 1:
            print("error, try one more time")
            crawl_url(config["URLS_TO_CHECK"][1], config)
        else:
            print("error")

if __name__ == '__main__':
    main()
