# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EbayToAmazon(scrapy.Item):
    ebay_isbn = scrapy.Field()
    ebay_price = scrapy.Field()
    ebay_link = scrapy.Field()
    amazon_price = scrapy.Field()
    amazon_offer_type = scrapy.Field()
    amazon_link = scrapy.Field()
    amazon_isbn = scrapy.Field()