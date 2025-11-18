from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Platform(models.Model):
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    title = models.CharField(max_length=100)
    product_id = models.CharField(max_length=12, unique=True, blank=True, null=True)

    def __str__(self):
        return self.title


class Genre(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Game(models.Model):
    title = models.CharField()
    slug = models.SlugField(blank=True, null=True)
    description = models.TextField(blank=True)
    short_description = models.TextField(blank=True, null=True)
    developer_name = models.CharField(max_length=100, blank=True, null=True)
    publisher_name = models.CharField(max_length=100, blank=True, null=True)
    release_date = models.DateField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True, related_name='games')
    platforms = models.ManyToManyField(Platform, blank=True, related_name='games', )
    subscriptions = models.ManyToManyField(Subscription, blank=True, related_name='games')
    product_id = models.CharField(max_length=12, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_in_gamepass(self):
        return any("Game Pass" in sub.title for sub in self.subscriptions.all())

    @property
    def is_in_eaplay(self):
        return any("EA Play" in sub.title for sub in self.subscriptions.all())

    @property
    def is_in_ubisoftplus(self):
        return any("Ubisoft+" in sub.title for sub in self.subscriptions.all())

    @property
    def is_in_gtaplus(self):
        return any("GTA+" in sub.title for sub in self.subscriptions.all())

    def __str__(self):
        return self.title


class GameImage(models.Model):
    IMAGE_TYPES = [
        ('box_art', 'Box Art'),
        ('poster', 'Poster'),
        ('hero_art', 'Hero Art'),
        ('screenshot', 'Screenshot'),
        ('logo', 'Logo'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='images')
    image_type = models.CharField(max_length=20, choices=IMAGE_TYPES)
    url = models.URLField()
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('game', 'image_type')

    def __str__(self):
        return f"{self.game.title} - {self.get_image_type_display()}"


class GameVideo(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=100)
    url = models.URLField()
    type = models.CharField(max_length=100)
    height = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    preview_image_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f'{self.title} - {self.type}'


class Region(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    currency_code = models.CharField(max_length=3)
    currency_symbol = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.name} ({self.currency_code})"


class Store(models.Model):
    name = models.CharField(max_length=100)
    base_url = models.URLField()

    def __str__(self):
        return self.name


class Price(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='prices')
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    base_price = models.DecimalField(decimal_places=2, max_digits=10)
    current_price = models.DecimalField(decimal_places=2, max_digits=10)
    discount_percentage = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ]
    )

    is_on_sale = models.BooleanField(default=False)
    sale_start_date = models.DateField(null=True, blank=True)
    sale_end_date = models.DateField(null=True, blank=True)

    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('game', 'region', 'store')

    def __str__(self):
        currency = self.region.currency_symbol
        if self.is_on_sale:
            return f"{self.game.title} - {currency}{self.current_price} ({currency}{self.base_price})"
        else:
            return f"{self.game.title} - {currency}{self.base_price}"

    def save(self, *args, **kwargs):
        if self.current_price < self.base_price:
            self.is_on_sale = True
            self.discount_percentage = round(
                (self.base_price - self.current_price) / self.base_price * 100
            )
        else:
            self.is_on_sale = False
            self.discount_percentage = 0

        super().save(*args, **kwargs)
