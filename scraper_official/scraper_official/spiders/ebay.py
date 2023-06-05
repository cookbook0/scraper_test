import scrapy
import random
from scraper_official.items import EbayToAmazon
from scraper_official.pipelines import CSVPipeline

user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', ]


class EbaySpider(scrapy.Spider):
    name = 'ebay'
    custom_settings = {'ITEM_PIPELINES': {'scraper_official.pipelines.CSVPipeline': 300}}
    ebay_headers = {
        'User-Agent': random.choice(user_agents), 'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.ebay.com/'}

    amazon_headers = {
        'User-Agent': random.choice(user_agents), 'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.amazon.com/'}
    page_number = 3
    item = EbayToAmazon()
    total_listings = 240
    listings_parsed = 0

    # begin ebay requests using keyword, and pass to "get_listings"
    def start_requests(self):
        search_term = input('Ebay Search: ')
        page = str(self.page_number)
        start_url = f'https://www.ebay.com/sch/i.html?_nkw={search_term}&LH_BIN=1&_ipg=240&_pgn={page}'

        yield scrapy.Request(start_url, headers=self.ebay_headers, callback=self.get_listings)

    # take request and pass all book listings to "parse_info" , find next page href and loop
    def get_listings(self, response):
        try:
            if response.status == 200:
                listings = response.css('a.s-item__link::attr(href)').getall()[1:]

                for link in listings:
                    yield scrapy.Request(link, headers=self.ebay_headers, callback=self.parse_info)
                    self.listings_parsed += 1

                    if self.listings_parsed >= self.total_listings:
                        break

                if self.listings_parsed >= self.total_listings:
                    return

                next_page = response.css('a.pagination__next::attr(href)').get()

                if next_page:
                    yield scrapy.Request(next_page, headers=self.ebay_headers, callback=self.get_listings)
            else:
                print("non 200 received")
        except Exception as e:
            self.logger.error("Error occurred while processing eBay response: %s", str(f'{e}here it is'))

    # parse book price and isbn, send ISBN to start_amazon
    def parse_info(self, response):
        isbn = response.css('span[itemprop="productID"] span.ux-textspans::text').get()
        isbn2 = response.css('span[itemprop="gtin13"] div span::text').get()

        if isbn:
            self.item['ebay_isbn'] = isbn  # ebay isbn
            self.item['ebay_link'] = response.url  # ebay_link
            price = response.css('div.x-price-primary span.ux-textspans::text').get()
            price_str = price.replace('US $', '')
            self.item['ebay_price'] = float(price_str)  # ebay price
            yield from self.start_amazon(isbn, self.item)

        elif isbn2:
            self.item['ebay_isbn'] = isbn2  # ebay isbn
            price = response.css('div.x-price-primary span.ux-textspans::text').get()
            price_str = price.replace('US $', '')
            self.item['ebay_price'] = float(price_str)  # ebay price
            yield from self.start_amazon(isbn2, self.item)

    # use ebay ISBN to make amazon request, send to "get_amazon_listing"
    def start_amazon(self, isbn, item):
        url = f"https://www.amazon.com/s?k={isbn}"  # amazon link
        yield scrapy.Request(url, headers=self.amazon_headers, callback=self.get_amazon_listing,
                             meta={'item': item})

    # find href of the first listing, formulate a URL and send request to "parse_amazon"
    def get_amazon_listing(self, response):
        item = response.meta['item']
        href = response.css('div.s-product-image-container a.a-link-normal::attr(href)').get()
        href_str = str(href)

        listing = f'https://amazon.com{href_str}'  # book link
        item['amazon_link'] = listing

        yield scrapy.Request(listing, headers=self.amazon_headers, callback=self.parse_amazon,
                             meta={'item': item})

    # get amazon book used price. first try buybox, then try the lowest used offer
    def parse_amazon(self, response):
        item = response.meta['item']
        bb = response.css('div#usedAccordionRow h5 span#usedPrice::text').get()
        bb2 = response.css('div#usedOnlyBuybox span.a-size-base.a-color-price.offer-price.a-text-normal::text').get()
        price = response.css('apan.tmm-olp-links span.olp-used olp-link a.a-size-mini a-link-normal::text').get()
        isbn_13 = response.xpath('//li[contains(span/text(), "ISBN-13")]/span[2]/text()').get()
        if isbn_13:
            isbn_13 = isbn_13.strip()

        if bb:
            bb_str = bb.replace('US $', '')
            item['amazon_price'] = float(bb_str)
            item['amazon_offer_type'] = 'BB'
            item['amazon_isbn'] = isbn_13
        elif bb2:
            bb2_str = bb2.replace('US $', '')
            item['amazon_price'] = float(bb2_str)
            item['amazon_offer_type'] = 'BB'
            item['amazon_isbn'] = isbn_13
        elif price:
            item['amazon_price'] = float(price)
            item['amazon_offer_type'] = 'Lowest Offer'
            item['amazon_isbn'] = isbn_13
        else:
            item['amazon_price'] = 'Price Failed'
            item['amazon_offer_type'] = 'N/A'
            item['amazon_isbn'] = isbn_13
        yield item
