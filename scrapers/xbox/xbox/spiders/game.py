import json
import re

import scrapy

from ..items import XboxItem


class GameSpider(scrapy.Spider):
    name = "game"
    allowed_domains = ["www.xbox.com", "xboxservices.com"]
    start_urls = ["https://www.xbox.com/en-US/games/browse"]

    def __init__(self, max_pages=3, *args, **kwargs):
        super(GameSpider, self).__init__(*args, **kwargs)

        self.max_pages = int(max_pages)
        self.api_url = "https://emerald.xboxservices.com/xboxcomfd/browse?locale=en-US"
        self.cv_base = "DSK6KO20k6Y7NXCBkdtipF"
        self.cv_counter = 1

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        script_pattern = r'window\.__PRELOADED_STATE__ = ({.*?});'
        match = re.search(script_pattern, response.text, re.DOTALL)

        if not match:
            self.logger.warning("Could not find preloaded state")
            return

        try:
            preloaded_data = json.loads(match.group(1))
        except json.decoder.JSONDecodeError as e:
            self.logger.error(f"Error decoding preloaded state: {e}")
            return

        products = preloaded_data.get('core2', {}).get('channels', {}).get('productSummaries', {})
        channel_data = preloaded_data.get('core2', {}).get('channels', {}).get('channelData', {})

        channel_key = [k for k in channel_data.keys() if 'BROWSE_CHANNELID' in k][0]
        game_ids = channel_data.get(channel_key, {}).get('data', {}).get('products', [])

        for game_info in game_ids:
            game_id = game_info.get('productId')
            if game_id and game_id in products:
                game_data = products[game_id]
                yield self.parse_item(game_data)

        continuation_token = channel_data.get(channel_key, {}).get('data', {}).get('encodedCT')
        if continuation_token:
            yield self.create_api_request(continuation_token)

    def create_api_request(self, continuation_token):
        self.logger.info(f"Creating API request for page {self.cv_counter}")
        ms_cv = f"{self.cv_base}.{self.cv_counter}"
        self.cv_counter += 1

        body = {
            'Filters': 'e30=',
            'ReturnFilters': False,
            'ChannelKeyToBeUsedInResponse': 'BROWSE_CHANNELID=_FILTERS=',
            'EncodedCT': continuation_token,
            'ChannelId': ''
        }

        if self.cv_counter <= self.max_pages:
            return scrapy.Request(
                url=self.api_url,
                method='POST',
                headers={'MS-CV': ms_cv},
                body=json.dumps(body),
                callback=self.parse_api_response,
            )
        else:
            raise scrapy.exceptions.CloseSpider(reason=f"Closing API request for page {self.cv_counter}")

    def parse_api_response(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing API response: {e}")
            return

        games = data.get('productSummaries', [])
        channel_data = data.get('channels', {})
        channel_key = [k for k in channel_data.keys() if 'BROWSE_CHANNELID' in k][0]

        for game_data in games:
            yield self.parse_item(game_data)

        next_continuation_token = channel_data.get(channel_key, {}).get('encodedCT')
        if next_continuation_token:
            yield self.create_api_request(next_continuation_token)

    def parse_item(self, game_data):
        item = XboxItem()

        item['game_title'] = game_data.get('title')
        item['game_description'] = game_data.get('description')
        item['game_short_description'] = game_data.get('shortDescription', '')
        item['game_developer_name'] = game_data.get('developerName')
        item['game_publisher_name'] = game_data.get('publisherName')
        item['game_release_date'] = game_data.get('releaseDate')
        item['xbox_product_id'] = game_data.get('productId')
        item['images'] = game_data.get('images')

        if 'specificPrices' in game_data and game_data['specificPrices']['purchaseable']:
            price_data = game_data['specificPrices']['purchaseable'][0]
            item['price_base'] = price_data.get('msrp')
            item['price_current'] = price_data.get('listPrice')

        self.logger.info(f"Parsed item: {item.get('game_title')}")
        return item
