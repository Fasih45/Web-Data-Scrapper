import os
import requests
import time
import json  # Added import for json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service  # Added import for Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# Function to extract data from the webpage
def extract_data(driver, folder):
    img_sources = []  # List to store image sources
    videos = []  # List to store video URLs
    links = []  # List to store link URLs
    texts = []  # List to store text content

    # Extract image sources
    for img in driver.find_elements(By.TAG_NAME, 'img'):
        img_url = img.get_attribute('src')
        img_sources.append(img_url)
        download_image(img_url, folder)  # Download and save image

    # Extract videos
    for video in driver.find_elements(By.TAG_NAME, 'video'):
        video_url = video.get_attribute('src')
        videos.append(video_url)

    # Extract links
    for link in driver.find_elements(By.TAG_NAME, 'a'):
        link_url = link.get_attribute('href')
        links.append(link_url)

    # Extract text
    for tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div']:
        for element in driver.find_elements(By.TAG_NAME, tag):
            texts.append(element.text)

    return img_sources, videos, links, texts

# Function to save data to a CSV file
def save_to_csv(data, filename):
    # Convert data to DataFrame
    df = pd.DataFrame(data, columns=['Value'])
    # Save DataFrame to CSV file
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

# Function to download images
def download_image(url, folder):
    try:
        # Extract filename from URL
        filename = os.path.join(folder, url.split('/')[-1].split('?')[0])
        # Download image and save to specified folder
        with open(filename, 'wb') as f:
            response = requests.get(url)
            if response.status_code == 200:
                f.write(response.content)
            else:
                print(f"Failed to download image from {url}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
    except FileNotFoundError as e:
        print(f"Error: The specified folder '{folder}' does not exist.")

# Function to scroll to the bottom of the page
def scroll_to_bottom(driver):
    # Scroll to the bottom of the page
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # Wait for some time for the new content to load
    time.sleep(2)

# Function to scrape data from the webpage and save it
def scrape_and_save(url, folder):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')  # Run Chrome in headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    try:
        # Scroll to the bottom of the page multiple times to load all content
        for _ in range(5):  # Adjust the range based on the length of the page and the amount of content
            scroll_to_bottom(driver)

        # Extract data from the webpage
        img_sources, videos, links, texts = extract_data(driver, folder)

        # Combine all data into a single list of dictionaries
        data = []
        # Convert image URLs to dictionary format and append to data list
        for source in img_sources:
            data.append({'type': 'image', 'url': source})
        # Convert video URLs to dictionary format and append to data list
        for video in videos:
            data.append({'type': 'video', 'url': video})
        # Convert link URLs to dictionary format and append to data list
        for link in links:
            data.append({'type': 'link', 'url': link})
        # Convert text content to dictionary format and append to data list
        for text in texts:
            data.append({'type': 'text', 'content': text})

        # Save the combined data in a single JSONL file
        with open('mastodon.jsonl', 'w') as f:
            # Write each item in data list as a JSON object to the file
            for item in data:
                json.dump(item, f)
                f.write('\n')

        print("Data saved to mastodon.jsonl")
    finally:
        driver.quit()

if __name__ == "__main__":
    url = 'https://mastodon.social/explore'
    folder = 'Images'  # specify the folder where you want to save images
    if not os.path.exists(folder):
        os.makedirs(folder)
    scrape_and_save(url, folder)
