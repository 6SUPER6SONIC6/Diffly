from django.contrib import admin

from .models import Platform, Region, Price, GameImage, Game, Subscription, GameVideo, Genre


class PriceInline(admin.TabularInline):
    model = Price
    extra = 0

class GameImageInline(admin.TabularInline):
    model = GameImage
    extra = 0

class GameVideoInline(admin.TabularInline):
    model = GameVideo
    extra = 0

class GameAdmin(admin.ModelAdmin):
    inlines = [PriceInline, GameImageInline, GameVideoInline]
    list_filter = ('title',)
    search_fields = ('title', 'product_id')

admin.site.register(Game, GameAdmin)
admin.site.register(Platform)
admin.site.register(Region)
admin.site.register(Subscription)
admin.site.register(Genre)
