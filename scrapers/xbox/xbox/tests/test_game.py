import json
import unittest
from unittest.mock import Mock

from scrapy import Request
from scrapy.http import HtmlResponse

from ..items import XboxItem
from ..spiders.game import GameSpider


class GameSpiderTest(unittest.TestCase):
    def setUp(self):
        self.spider = GameSpider()
        self.example_html = """
    <html>
<head>
    <script>
    window.__PRELOADED_STATE__ = {
        "core2": {
            "channels": {
                "channelData": {
                    "BROWSE_CHANNELID=_FILTERS=ORDERBY=TITLE ASC&PLAYWITH=XBOXONE,XBOXSERIESX|S": {
                        "data": {
                            "products": [
                                {"productId": "1"},
                                {"productId": "2"}
                            ],
                            "encodedCT": "TOKEN1"
                        }
                    }
                }
            },
            "products": {
                "productSummaries": {
                    "1": {
                        "description": "Desc 1",
                        "developerName": "Dev 1",
                        "images": {
                            "boxArt": {"url": "game/1/boxArt", "width": 2160, "height": 2160}
                        },
                        "productId": "1",
                        "publisherName": "Pub 1",
                        "releaseDate": "2024-11-25T05:00:00.0000000Z",
                        "shortDescription": "Short desc 1",
                        "specificPrices": {
                            "purchaseable": [
                                {"listPrice": 89.99, "msrp": 89.99}
                            ]
                        },
                        "title": "Game 1"
                    },
                    "2": {
                        "description": "Desc 2",
                        "developerName": "Dev 2",
                        "images": {
                            "boxArt": {"url": "game/2/boxArt", "width": 2160, "height": 2160}
                        },
                        "productId": "2",
                        "publisherName": "Pub 2",
                        "releaseDate": "2020-07-16T00:00:00.0000000Z",
                        "shortDescription": "Short desc 2",
                        "specificPrices": {
                            "purchaseable": [
                                {"listPrice": 60, "msrp": 80}
                            ]
                        },
                        "title": "Game 2"
                    }
                }
            }
        }
    };
</script>
</head>
<body>
</body>
</html>
        """
        self.response = HtmlResponse(
            url="https://www.xbox.com/en-US/games/browse?orderby=Title+Asc&PlayWith=XboxSeriesX%7CS%2CXboxOne",
            body=self.example_html,
            encoding="utf-8",
        )

    def test_parse_scrapes_all_items(self):
        """Test that parse method extracts correct number of game items and API requests."""

        results = list(self.spider.parse(self.response))

        game_items = [item for item in results if isinstance(item, XboxItem)]
        api_requests = [item for item in results if isinstance(item, Request)]

        self.assertEqual(len(game_items), 2)
        self.assertEqual(len(api_requests), 1)

    def test_parse_scrapes_correct_game_information(self):
        """Test that parse method correctly extracts and maps game data fields."""

        results_generator = self.spider.parse(self.response)

        game_1 = next(results_generator)
        self.assertEqual(game_1['product_id'], "1")
        self.assertEqual(game_1['game_title'], "Game 1")
        self.assertEqual(game_1['game_description'], "Desc 1")
        self.assertEqual(game_1['game_short_description'], "Short desc 1")
        self.assertEqual(game_1['game_publisher_name'], "Pub 1")
        self.assertEqual(game_1['price_base'], 89.99)
        self.assertEqual(game_1['price_current'], 89.99)
        self.assertEqual(game_1['game_release_date'], "2024-11-25T05:00:00.0000000Z")

        game_2 = next(results_generator)
        self.assertEqual(game_2['product_id'], "2")
        self.assertEqual(game_2['game_title'], "Game 2")
        self.assertEqual(game_2['game_description'], "Desc 2")
        self.assertEqual(game_2['game_short_description'], "Short desc 2")
        self.assertEqual(game_2['game_publisher_name'], "Pub 2")
        self.assertEqual(game_2['price_base'], 80)
        self.assertEqual(game_2['price_current'], 60)
        self.assertEqual(game_2['game_release_date'], "2020-07-16T00:00:00.0000000Z")

    def test_parse_handles_invalid_json(self):
        """Test that spider handles malformed JSON gracefully"""

        invalid_html = """
                <html>
                <head>
                    <script>
                    window.__PRELOADED_STATE__ = {'invalid': 'JSON'};
                    </script>
                </head>
                </html>
                """
        response = HtmlResponse(
            url="https://www.xbox.com/en-US/games/browse",
            body=invalid_html,
            encoding="utf-8",
        )

        results = list(self.spider.parse(response))
        self.assertEqual(len(results), 0)

    def test_parse_handles_missing_preloaded_state(self):
        """Test spider behavior when __PRELOADED_STATE__ script is missing"""
        html_without_preloaded_state = """
                <html>
                <head>
                    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
                    <meta charset="utf-8"/>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title data-react-helmet="true">Browse all games | Xbox</title>
                    <script type="text/javascript"> </script>
                </head>

                  <body data-theme="dark">
                    <div id="root">
                            <div>
                            </div>
                <div class="appBackground">
                </div>
                </div>
                </body>

                </html>
        """
        response = HtmlResponse(
            url="https://www.xbox.com/en-US/games/browse",
            body=html_without_preloaded_state,
            encoding="utf-8",
        )
        results = list(self.spider.parse(response))
        self.assertEqual(len(results), 0)

    def test_parse_creates_api_request(self):
        """Test that parse method generates correct API request for pagination."""

        results = list(self.spider.parse(self.response))
        api_requests = [r for r in results if isinstance(r, Request)]
        self.assertEqual(len(api_requests), 1)
        request = api_requests[0]
        self.assertEqual(request.method, "POST")
        self.assertIn("emerald.xboxservices.com", request.url)
        self.assertIn("en-US", request.url)

    def test_create_api_request_structure(self):
        """Test that create_api_request builds properly formatted API requests."""

        continuation_token = 'test_ct'
        region = 'en-US'

        request = self.spider.create_api_request(continuation_token, region)

        self.assertIsInstance(request, Request)
        self.assertEqual(request.method, "POST")
        self.assertIn("emerald.xboxservices.com", request.url)
        self.assertIn(region, request.url)
        self.assertIn("Ms-Cv", request.headers)

        body_data = json.loads(request.body)
        self.assertEqual(body_data['EncodedCT'], continuation_token)
        self.assertIn('Filters', body_data)
        self.assertIn('ChannelKeyToBeUsedInResponse', body_data)

    def test_parse_api_response_handles_invalid_json(self):
        """Test API response parsing with malformed JSON from Xbox Store API."""
        response = Mock()
        response.text = "{'invalid': 'JSON'}"
        response.meta = {'region': 'en-US'}

        results = list(self.spider.parse_api_response(response))
        self.assertEqual(len(results), 0)

    def test_parse_item_handles_missing_fields(self):
        """Test parse_item with minimal game data"""
        minimal_game_data = {
            'region': 'en-US',
            'productId': '123',
            'title': 'Game1'
        }

        item = self.spider.parse_item(minimal_game_data)

        self.assertEqual(item['region'], 'en-US')
        self.assertEqual(item['product_id'], '123')
        self.assertEqual(item['game_title'], 'Game1')
        self.assertIsNone(item.get('game_description'))
        self.assertEqual(item.get('game_short_description'), '')
        self.assertIsNone(item.get('price_base'))

    def test_ms_cv_increments(self):
        """Test that MS-CV correlation vector counter increments correctly."""

        initial_counter = self.spider.cv_counter

        request_1 = self.spider.create_api_request('ct1', 'en-US')
        request_2 = self.spider.create_api_request('ct2', 'en-US')

        cv_1 = request_1.headers.get('Ms-Cv').decode()
        cv_2 = request_2.headers.get('Ms-Cv').decode()

        counter_1 = int(cv_1.split('.')[-1])
        counter_2 = int(cv_2.split('.')[-1])

        self.assertEqual(counter_1, initial_counter)
        self.assertEqual(counter_2, initial_counter + 1)

    def test_pagination_respects_max_pages(self):
        """Test that pagination stops when max_pages limit is reached."""
        spider = GameSpider(max_pages=1)
        spider.pages_scraped['en-US'] = 1  # Max
        api_response_body = {
            'productSummaries': [],
            'channels': {
                'BROWSE_CHANNELID=_FILTERS=ORDERBY=TITLE ASC&PLAYWITH=XBOXONE,XBOXSERIESX|S':
                    {
                        'encodedCT': 'next_ct'
                    }
            }
        }

        response = Mock()
        response.text = json.dumps(api_response_body)
        response.meta = {'region': 'en-US'}

        results = list(spider.parse_api_response(response))

        api_requests = [r for r in results if isinstance(r, Request)]
        self.assertEqual(len(api_requests), 0)


if __name__ == '__main__':
    unittest.main()
