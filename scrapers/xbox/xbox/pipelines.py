# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from asgiref.sync import sync_to_async
from django.db import close_old_connections
from django.utils import timezone
from django.utils.dateparse import parse_datetime

# useful for handling different item types with a single interface
from apps.games.models import *


class DjangoModelPipeline:

    async def process_item(self, item, spider):
        spider.logger.info(
            f'Saving item: {item.get("product_id")}({item.get('game_title')}) from region {item.get("region")}')
        platform = await sync_to_async(Platform.objects.get)(name='Xbox')
        game, _ = await sync_to_async(Game.objects.get_or_create)(product_id=item['product_id'])

        if item.get('region') == 'en-US':
            try:
                release_date = parse_datetime(item.get('game_release_date'))
            except TypeError:
                release_date = None

            await sync_to_async(Game.objects.filter(product_id=item['product_id']).update)(
                title=item.get('game_title'),
                description=item.get('game_description', ''),
                short_description=item.get('game_short_description', ''),
                developer_name=item.get('game_developer_name', ''),
                publisher_name=item.get('game_publisher_name', ''),
                release_date=release_date,
            )

        game_platform, _ = await sync_to_async(GamePlatform.objects.get_or_create)(
            platform=platform,
            game=game,
        )

        if not item.get('price_base') or not item.get('price_current'):
            spider.logger.warning(f'No price for {item.get("product_id")} in {item.get("region")}')

        if "price_base" in item and "region" in item:
            region_code = item['region'][3:]
            region = await sync_to_async(Region.objects.get)(code=region_code)
            store, created = await sync_to_async(Store.objects.get_or_create)(
                name=f'Xbox Store {region_code}',
                defaults={
                    'base_url': f'https://www.xbox.com/{item.get("region")}',
                }
            )
            if created:
                store.platforms.add(platform)

            price, _ = await sync_to_async(Price.objects.update_or_create)(
                game=game,
                platform=platform,
                region=region,
                store=store,
                defaults={
                    'base_price': item.get('price_base'),
                    'current_price': item.get('price_current'),
                    'last_updated': timezone.now(),
                }
            )

        if 'images' in item and item['images']:
            for image_type, data in item.get('images', {}).items():
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
                game_image, _ = await sync_to_async(GameImage.objects.update_or_create)(
                    game=game,
                    image_type=image_type,
                    defaults={
                        'url': data['url'],
                        'width': data['width'],
                        'height': data['height'],
                    }
                )

        return item

    def close_spider(self, spider):
        close_old_connections()
