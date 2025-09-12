from django.contrib import admin

from .models import Platform, Region, Price, GameImage, Game


class PriceInline(admin.TabularInline):
    model = Price
    extra = 0

class GameImageInline(admin.TabularInline):
    model = GameImage
    extra = 0

class GameAdmin(admin.ModelAdmin):
    inlines = [PriceInline, GameImageInline]
    list_filter = ('title',)
    search_fields = ('title',)

admin.site.register(Game, GameAdmin)
admin.site.register(Platform)
admin.site.register(Region)
