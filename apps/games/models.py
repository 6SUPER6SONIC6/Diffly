from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Platform(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    short_description = models.TextField(blank=True)
    developer_name = models.CharField(max_length=100, blank=True)
    publisher_name = models.CharField(max_length=100, blank=True)
    release_date = models.DateField(null=True, blank=True)
    platforms = models.ManyToManyField(
        Platform,
        through='GamePlatform',
        related_name='games',
    )
    product_id = models.CharField(max_length=12, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class Region(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    currency_code = models.CharField(max_length=3)
    currency_symbol = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.name} ({self.currency_code})"


class GamePlatform(models.Model):
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('platform', 'game')

    def __str__(self):
        return f"{self.game.title} - {self.platform.name}"


class Store(models.Model):
    name = models.CharField(max_length=100)
    base_url = models.URLField()
    platforms = models.ManyToManyField(Platform, related_name='stores')

    def __str__(self):
        return self.name


class Price(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='prices')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    base_price = models.DecimalField(decimal_places=2, max_digits=10)
    current_price = models.DecimalField(decimal_places=2, max_digits=10)
    discount_percentage = models.DecimalField(
        decimal_places=2,
        max_digits=5, default=Decimal('0.00'),
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
        unique_together = ('game', 'platform', 'region', 'store')

    def __str__(self):
        currency = self.region.currency_symbol
        if self.is_on_sale:
            return f"{self.game.title} - {currency}{self.current_price} ({currency}{self.base_price})"
        else:
            return f"{self.game.title} - {currency}{self.base_price}"

    def save(self, *args, **kwargs):
        if self.current_price < self.base_price:
            self.is_on_sale = True
            self.discount_percentage = (
                    (self.base_price - self.current_price) / self.base_price * 100
            ).quantize(Decimal('0.01'))
        else:
            self.is_on_sale = False
            self.discount_percentage = Decimal('0.00')

        super().save(*args, **kwargs)
