# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PackageItem(scrapy.Item):
    package_id = scrapy.Field()
    name = scrapy.Field()
    version = scrapy.Field()
    display_name = scrapy.Field()
    description = scrapy.Field()
    kind = scrapy.Field()
    readme = scrapy.Field()
    file_urls = scrapy.Field()
    logo_image_id = scrapy.Field()
    file_names = scrapy.Field()
    files = scrapy.Field()
    repository_name = scrapy.Field()
    category = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    normalized_name = scrapy.Field()
