from django.db import models


class Platform(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    title = models.CharField(max_length=100)
    cover_image = models.URLField(blank=True)
    platforms = models.ManyToManyField(
        Platform,
        through='GamePlatform',
        related_name='games',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


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


class Price(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    price_value = models.DecimalField(decimal_places=2, max_digits=10)
    store_url = models.URLField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('game', 'platform', 'region')

    def __str__(self):
        return f"{self.game.title} - {self.region.currency_symbol}{self.price_value}"
