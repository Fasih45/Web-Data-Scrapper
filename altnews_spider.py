import os
import requests
import scrapy
import json

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
                print(f"Image downloaded successfully: {filename}")
            else:
                print(f"Failed to download image from {url}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
    except FileNotFoundError as e:
        print(f"Error: The specified folder '{folder}' does not exist.")

# Scrapy spider class for Altnews website
class AltnewsSpiderSpider(scrapy.Spider):
    name = "altnews_spider"
    allowed_domains = ["www.altnews.in"]
    start_urls = ["https://www.altnews.in"]

    # Parse method to extract information from the response
    def parse(self, response):
        # Extracting information from individual articles
        for article in response.css('article'):
            # Extract image URL
            image_url = article.css('div.post-thumbnail div.thumb-w img::attr(src)').get()
            if image_url:
                download_image(image_url, 'images')  # Download the image
            # Create item dictionary for article information
            item = {
                'Tag': 'Article',
                'URL': article.css('h4.entry-title a::attr(href)').get(),
                'Image URL': image_url,
                'Title': article.css('h4.entry-title a::text').get(),
                'Date': article.css('div.entry-meta time::text').get(),
                'Author': article.css('div.entry-meta span.byline a::text').get(),
            }
            self.write_to_jsonl(item)  # Write item to JSONL file

        # Extracting latest videos
        latest_videos = response.css("div.widget-title-wrapper.w-t-w:contains('Latest Videos') + div.widget-container.widget_text.enhanced-text-widget")
        for video in latest_videos:
            # Extract video URL
            video_url = video.css('span.embed-youtube div.fluid-width-video-wrapper iframe.youtube-player::attr(src)').get()
            if video_url:
                item = {'Tag': 'Video', 'Video URL': video_url}
                self.write_to_jsonl(item)  # Write item to JSONL file

        # Follow pagination links to crawl additional pages
        for link in response.css('article h4.entry-title a::attr(href)').getall():
            yield response.follow(link, callback=self.parse_article)

        # Follow pagination links to crawl additional pages
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    # Parse method for individual article pages
    def parse_article(self, response):
        # Extracting the article content
        paragraphs = response.css('div.entry-content p::text').getall()
        content = ' '.join(paragraphs).strip()

        # Extracting the date
        date = response.css('div.entry-meta time::text').get()

        # Extracting the author
        author = response.css('div.entry-meta span.byline a::text').get()

        # Extracting the URL
        url = response.url

        # Create item dictionary for article information
        item = {
            'Tag': 'Article',
            'URL': url,
            'Content': content,
            'Date': date.strip() if date else None,
            'Author': author.strip() if author else None
        }
        self.write_to_jsonl(item)  # Write item to JSONL file

    # Method to write item to JSONL file
    def write_to_jsonl(self, item):
        with open('output.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(item) + '\n')
