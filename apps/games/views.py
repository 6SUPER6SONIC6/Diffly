from django.db.models import Prefetch
from django.shortcuts import render
from django.views import generic

from apps.games.models import Game, Price, GameImage


def index(request):
    latest_releases = Game.objects.exclude(
        title__isnull=True
    ).exclude(
        title__exact=""
    ).exclude(
        release_date__exact=None
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=GameImage.objects.filter(
                image_type__in=['box_art', 'poster', 'hero_art']
            )
        )
    ).order_by('-release_date')[:4]

    discounted_games = Game.objects.exclude(
        title__isnull=True
    ).exclude(
        title__exact=""
    ).filter(
        prices__is_on_sale=True,
        prices__discount_percentage__gt=0
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=GameImage.objects.filter(
                image_type__in=['box_art', 'poster', 'hero_art']
            )
        ),
        Prefetch(
            'prices',
            queryset=Price.objects.filter(
                is_on_sale=True
            ).select_related('region')
        )
    ).distinct().order_by('-prices__discount_percentage')[:4]

    context = {
        'latest_releases': latest_releases,
        'discounted_games': discounted_games,
    }
    return render(request, 'games/index.html', context)


class GameListView(generic.ListView):
    template_name = 'games/game_list.html'
    context_object_name = 'game_list'
    queryset = Game.objects.exclude(title__isnull=True).exclude(title__exact="").order_by('title')
    paginate_by = 30


class GameDetailView(generic.DetailView):
    model = Game
    template_name = 'games/game_detail.html'


class SearchView(generic.ListView):
    template_name = 'games/search.html'
    context_object_name = 'game_list'
    paginate_by = 30

    def get_queryset(self):
        query = self.request.GET.get("q")
        if query:
            return Game.objects.filter(title__icontains=query).exclude(title__exact="").exclude(title__isnull=True)
        return Game.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
