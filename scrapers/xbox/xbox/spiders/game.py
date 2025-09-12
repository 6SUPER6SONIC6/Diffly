import json
import re

import scrapy

from ..items import XboxItem


class GameSpider(scrapy.Spider):
    name = "game"
    allowed_domains = ["www.xbox.com", "xboxservices.com"]
    regions = ["en-US", "tr-TR"]

    def __init__(self, max_pages=3, *args, **kwargs):
        super(GameSpider, self).__init__(*args, **kwargs)

        self.max_pages = int(max_pages)
        self.pages_scraped = {region: 0 for region in self.regions}

        self.base_api_url = "https://emerald.xboxservices.com/xboxcomfd/browse?locale="
        self.cv_base = "DSK6KO20k6Y7NXCBkdtipF"
        self.cv_counter = 1

    async def start(self):
        for region in self.regions:
            yield scrapy.Request(
                url=f"https://www.xbox.com/{region}/games/browse?orderby=Title+Asc&PlayWith=XboxSeriesX%7CS%2CXboxOne",
                callback=self.parse,
                meta={"region": region},
            )

    def parse(self, response):
        script_pattern = r'window\.__PRELOADED_STATE__ = ({.*?});'
        match = re.search(script_pattern, response.text, re.DOTALL)
        region = response.meta.get('region')

        if not match:
            self.logger.warning(f"Could not find preloaded state for region {region}")
            return

        self.pages_scraped[region] += 1
        self.logger.info(f"Processing page {self.pages_scraped[region]}/{self.max_pages} for region {region}")

        try:
            preloaded_data = json.loads(match.group(1))
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f"Error decoding preloaded state: {e}")
            return

        products = preloaded_data.get('core2', {}).get('products', {}).get('productSummaries', {})
        channel_data = preloaded_data.get('core2', {}).get('channels', {}).get('channelData', {})

        channel_key = [k for k in channel_data.keys() if 'BROWSE_CHANNELID' in k][0]
        game_ids = channel_data.get(channel_key, {}).get('data', {}).get('products', [])

        for game_info in game_ids:
            game_id = game_info.get('productId')
            if game_id and game_id in products:
                game_data = products[game_id]
                game_data['region'] = region
                yield self.parse_item(game_data)

        continuation_token = channel_data.get(channel_key, {}).get('data', {}).get('encodedCT')
        if continuation_token and self.pages_scraped[region] < self.max_pages:
            yield self.create_api_request(continuation_token, region)

    def create_api_request(self, continuation_token, region):
        ms_cv = f"{self.cv_base}.{self.cv_counter}"
        self.cv_counter += 1

        body = {
            'Filters': 'eyJvcmRlcmJ5Ijp7ImlkIjoib3JkZXJieSIsImNob2ljZXMiOlt7ImlkIjoiVGl0bGUgQXNjIn1dfSwiUGxheVdpdGgiOnsiaWQiOiJQbGF5V2l0aCIsImNob2ljZXMiOlt7ImlkIjoiWGJveFNlcmllc1h8UyJ9LHsiaWQiOiJYYm94T25lIn1dfX0=',
            'ReturnFilters': False,
            'ChannelKeyToBeUsedInResponse': 'BROWSE_CHANNELID=_FILTERS=ORDERBY=TITLE ASC&PLAYWITH=XBOXONE,XBOXSERIESX|S',
            'EncodedCT': continuation_token,
            'ChannelId': ''
        }

        return scrapy.Request(
            url=f"{self.base_api_url}{region}",
            method='POST',
            headers={'MS-CV': ms_cv},
            body=json.dumps(body),
            callback=self.parse_api_response,
            meta={'region': region},
        )

    def parse_api_response(self, response):
        region = response.meta.get('region')

        self.pages_scraped[region] += 1
        self.logger.info(f"Processing page {self.pages_scraped[region]}/{self.max_pages} for region {region}")

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing API response: {e}")
            return

        games = data.get('productSummaries', [])
        channel_data = data.get('channels', {})
        channel_key = [k for k in channel_data.keys() if 'BROWSE_CHANNELID' in k][0]

        for game_data in games:
            game_data['region'] = region
            yield self.parse_item(game_data)

        next_continuation_token = channel_data.get(channel_key, {}).get('encodedCT')
        if next_continuation_token and self.pages_scraped[region] < self.max_pages:
            yield self.create_api_request(next_continuation_token, region)

    def parse_item(self, game_data):
        item = XboxItem()

        item['region'] = game_data.get('region')
        item['game_title'] = game_data.get('title')
        item['game_description'] = game_data.get('description')
        item['game_short_description'] = game_data.get('shortDescription', '')
        item['game_developer_name'] = game_data.get('developerName')
        item['game_publisher_name'] = game_data.get('publisherName')
        item['game_release_date'] = game_data.get('releaseDate')
        item['product_id'] = game_data.get('productId')
        item['images'] = game_data.get('images')

        prices = game_data.get('specificPrices', {}).get('purchaseable', [])
        if prices:
            price_data = prices[0]
            item['price_base'] = price_data.get('msrp')
            item['price_current'] = price_data.get('listPrice')

        return item
