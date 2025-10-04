# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class XboxItem(scrapy.Item):
    game_title = scrapy.Field()
    game_description = scrapy.Field()
    game_short_description = scrapy.Field()
    game_developer_name = scrapy.Field()
    game_publisher_name = scrapy.Field()
    game_release_date = scrapy.Field()
    product_id = scrapy.Field()

    images = scrapy.Field()

    price_base = scrapy.Field()
    price_current = scrapy.Field()

    region = scrapy.Field()

