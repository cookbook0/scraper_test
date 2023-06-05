# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scraper_official.items import EbayToAmazon
import csv


class CSVPipeline:
    item = EbayToAmazon()

    def __init__(self):
        self.csv_file = open('output.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['ebay_isbn', 'link', 'E price', 'A price', 'amazon_isbn', 'amazon_link', 'offer_type'])

    def process_item(self, item, spider):
        self.csv_writer.writerow([
            item.get('ebay_isbn'),
            item.get('ebay_link'),
            item.get('ebay_price'),
            item.get('amazon_price'),
            item.get('amazon_isbn'),
            item.get('amazon_link'),
            item.get('amazon_offer_type')
        ])

    def close_spider(self, spider):
        self.csv_file.close()
