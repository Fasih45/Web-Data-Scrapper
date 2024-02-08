import os
import scrapy
import pandas as pd
import requests
import json

class TextSpider(scrapy.Spider):
    name = "textspider"
    allowed_domains = ["www.politifact.com"]
    start_urls = ["https://www.politifact.com"]

    def parse(self, response):
        # Extract data from article.m-statement
        statements = response.css('article.m-statement')
        for s in statements:
            item = {
                "Tag": "m-statement",
                "Source": s.css('.m-statement__author .m-statement__name::text').get(),
                "Description": s.css('.m-statement__desc::text').get(),
                "Headline": s.css('.m-statement__quote a::text').get(),
                "Arthur/date": s.css('.m-statement__footer::text').get(),
                "Image URL Thumb": s.css('.m-statement__image .c-image__thumb::attr(src)').get(),
                "Image URL Original": s.css('.m-statement__image .c-image__original::attr(src)').get(),
            }

            # Download the image
            if item['Image URL Original']:
                self.download_image(item['Image URL Original'], 'images')

            yield item

        # Extract data from m-teaser
        teasers = response.css('div.m-teaser, div.m-teaser--is-mini')
        for t in teasers:
            item = {
                "Tag": "m-teaser",
                "Title": t.css('h3.m-teaser__title a::text').get(),
                "Teaser Author/Date": t.css('.m-teaser__meta::text').get(),
                "Image URL Thumb (Teaser)": t.css('.m-teaser__img img.c-image__thumb::attr(src)').get(),
                "Image URL Original (Teaser)": t.css('.m-teaser__img img.c-image__original::attr(data-src)').get(),
            }

            # Download the teaser image
            if item['Image URL Original (Teaser)']:
                self.download_image(item['Image URL Original (Teaser)'], 'images')

            yield item

        # Follow pagination links to crawl additional pages
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        # Follow links to individual fact-check pages
        for link in response.css('div.m-statement__quote a::attr(href)').getall():
            yield response.follow(link, callback=self.parse_fact_check)

    def parse_fact_check(self, response):
        # Extracting the article content
        paragraphs = response.css('article.m-textblock p::text').getall()
        content = ' '.join(paragraphs).strip()

        # Extracting the date
        date = response.css('footer.m-statement__footer::text').get()

        # Extracting the author
        author = response.css('div.m-statement__meta a::text').get()

        # Extracting the URL
        url = response.url

        # Extracting the featured fact-check if present
        featured_fact_check = {
            "Author": response.css('.o-pick__header .m-statement__name::text').get(),
            "Description": response.css('.o-pick__header .m-statement__desc::text').get(),
            "Quote": response.css('.o-pick__content .m-statement__quote a::text').get(),
            "Date": response.css('.o-pick__content .m-statement__footer::text').get(),
        }

        data = {
            'Tag': 'fact-check',
            'URL': url,
            'Content': content,
            'Date': date.strip() if date else None,
            'Author': author.strip() if author else None,
            'Featured Fact Check': featured_fact_check
        }

        filename = 'politifact.jsonl'
        with open(filename, 'a') as f:
            f.write(json.dumps(data) + '\n')

        yield data

    def download_image(self, url, folder):
        try:
            filename = os.path.join(folder, url.split('/')[-1].split('?')[0])
            with open(filename, 'wb') as f:
                response = requests.get(url)
                if response.status_code == 200:
                    f.write(response.content)
                else:
                    self.logger.error(f"Failed to download image from {url}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading image from {url}: {e}")
        except FileNotFoundError as e:
            self.logger.error(f"Error: The specified folder '{folder}' does not exist.")
