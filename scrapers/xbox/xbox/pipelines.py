from collections import defaultdict
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.db import close_old_connections
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from scrapy.exceptions import DropItem

from apps.games.models import *

REGION_MAP = {
    "en-US": "US",
    "tr-TR": "TR",
    "ja-JP": "JP",
    "pl-PL": "PL",
    "en-GB": "UK",
    "en-CA": "CA",
    "ko-KR": "KR",
    "cs-CZ": "CZ",
    "de-DE": "EU",
}

SUBSCRIPTION_IDS = {
    "GAME_PASS_ULTIMATE": "CFQ7TTC0K6L8",
    "PC_GAME_PASS": "CFQ7TTC0KGQ8",
    "EA_PLAY": "CFQ7TTC0K5DH",
}


class DjangoModelPipeline:
    """Pipeline that saves scraped items into the Django database. Including games, platforms, images,
    and prices. Track statistics for created and updated records per region."""

    def __init__(self):
        """Initialize stats counters for tracking create/update operations."""
        self.stats = defaultdict(
            lambda: {
                'games': {'crt': 0, 'upd': 0},
                'prices': {'crt': 0, 'upd': 0},
                'images': 0,
                'videos': 0,
            }
        )

    async def process_item(self, item, spider):
        """Process each scraped item asynchronously, persist it to the database, update related models, and record
        statistics."""
        product_id = item.get('product_id')
        region = item.get('region')
        region_code = REGION_MAP.get(region)
        if not region_code:
            raise DropItem(f"Invalid region code {region} - {product_id}")

        # spider.logger.info(f"Saving item: {product_id}({item.get('game_title')}) from {region}")

        release_date = parse_datetime(item.get('game_release_date')) if item.get('game_release_date') else None
        if release_date:
            max_valid_date = timezone.now() + timedelta(days=365 * 3)
            if release_date > max_valid_date:
                release_date = None

        try:
            # Update game's metadata for the US region only
            game, created = await sync_to_async(Game.objects.update_or_create)(
                product_id=product_id,
                defaults={
                    'title': item.get('game_title'),
                    'slug': slugify(item.get('game_title')),
                    'description': item.get('game_description'),
                    'short_description': item.get('game_short_description'),
                    'developer_name': item.get('game_developer_name'),
                    'publisher_name': item.get('game_publisher_name'),
                    'release_date': release_date,
                } if region == 'en-US' else None,
            )
        except Exception as e:
            raise DropItem(f"Failed to create/get game {product_id}: {e}")
        else:
            if created:
                self.stats[region]['games']['crt'] += 1
            else:
                self.stats[region]['games']['upd'] += 1

        if region == 'en-US':
            images = item.get('images')
            videos = item.get('videos')
            genres = item.get('genres')
            platforms = item.get('platforms')

            if images:
                for image_type, image_data in images.items():
                    match image_type:
                        case 'boxArt':
                            image_type = 'box_art'
                        case 'poster':
                            image_type = 'poster'
                        case 'superHeroArt':
                            image_type = 'hero_art'
                        case 'screenshot':
                            image_type = 'screenshot'
                        case 'logo':
                            image_type = 'logo'
                        case _:
                            continue
                    try:
                        await sync_to_async(GameImage.objects.update_or_create)(
                            game=game,
                            image_type=image_type,
                            defaults={
                                'url': image_data['url'],
                                'width': image_data['width'],
                                'height': image_data['height'],
                            }
                        )
                    except Exception as e:
                        spider.logger.error(f"Failed to create/update image for {product_id}: {e}")
                    else:
                        self.stats[region]['images'] += 1

            if videos:
                for video in videos:
                    try:
                        await sync_to_async(GameVideo.objects.update_or_create)(
                            game=game,
                            url=video['url'],
                            defaults={
                                'title': video.get('title'),
                                'type': video.get('purpose'),
                                'height': video.get('height'),
                                'width': video.get('width'),
                                'preview_image_url': video.get('previewImage').get('url'),
                            }
                        )
                    except Exception as e:
                        spider.logger.error(f"Failed to create/update video for {product_id}: {e}")
                    else:
                        self.stats[region]['videos'] += 1

            if genres:
                genre_ids = []
                for genre_title in genres:
                    try:
                        genre = await sync_to_async(Genre.objects.get)(title=genre_title)
                    except Genre.DoesNotExist:
                        genre = await sync_to_async(Genre.objects.get)(title='Other')
                        genre_ids.append(genre.id)
                    else:
                        genre_ids.append(genre.id)

                await sync_to_async(game.genres.set)(genre_ids)

            if platforms:
                platform_ids = []
                for platform_code in platforms:
                    try:
                        platform = await sync_to_async(Platform.objects.get)(code=platform_code)
                    except Platform.DoesNotExist:
                        spider.logger.error(f"Failed to get platform for {product_id}: {platform_code}")
                    else:
                        platform_ids.append(platform.id)

                await sync_to_async(game.platforms.set)(platform_ids)

        if "price_base" in item and "region" in item:
            price_region = await sync_to_async(Region.objects.get)(code=region_code)
            store, created = await sync_to_async(Store.objects.get_or_create)(
                name=f'Xbox Store {region_code}',
                defaults={
                    'base_url': f'https://www.xbox.com/{region}',
                }
            )

            try:
                price, created = await sync_to_async(Price.objects.update_or_create)(
                    game=game,
                    region=price_region,
                    store=store,
                    defaults={
                        'base_price': item.get('price_base'),
                        'current_price': item.get('price_current'),
                        'store_url': f'https://www.xbox.com/{region}/games/store/{game.slug}/{game.product_id}' if game.slug else None,
                        'last_updated': timezone.now(),
                    }
                )
            except Exception as e:
                spider.logger.error(f"Failed to create/update price for {product_id}: {e}")
            else:
                if created:
                    self.stats[region]['prices']['crt'] += 1
                else:
                    self.stats[region]['prices']['upd'] += 1

        # Checking subscriptions that include a game only for the US region.
        if region == 'en-US':
            subscription_product_ids = set(item.get('subscriptions', []))

            if subscription_product_ids:
                if SUBSCRIPTION_IDS['EA_PLAY'] in subscription_product_ids:
                    subscription_product_ids.add(SUBSCRIPTION_IDS['GAME_PASS_ULTIMATE'])
                    subscription_product_ids.add(SUBSCRIPTION_IDS['PC_GAME_PASS'])

                subscription_ids = []
                for subscription_product_id in subscription_product_ids:
                    try:
                        subscription = await sync_to_async(Subscription.objects.get)(product_id=subscription_product_id)
                    except Subscription.DoesNotExist:
                        spider.logger.warning(
                            f"Unknown subscription product_id: {subscription_product_id} for game: {game.title}")
                    else:
                        subscription_ids.append(subscription.id)

                await sync_to_async(game.subscriptions.set)(subscription_ids)
            else:
                await sync_to_async(game.subscriptions.clear)()

        return item

    def close_spider(self, spider):
        """Log a summary of statistics and close database connection after the spider finishes."""
        for region, data in self.stats.items():
            spider.logger.info(
                f'''
                ---------------{region}---------------
                Games created: {data['games']['crt']}
                Games updated: {data['games']['upd']}
                Prices created: {data['prices']['crt']}
                Prices updated: {data['prices']['upd']}
                Images: {data['images']}
                Videos: {data['videos']}
                ---------------------------------------
                '''
            )
        close_old_connections()
