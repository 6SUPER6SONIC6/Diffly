from django.db.models import Prefetch, Q, F
from django.db.models.functions import Lower
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import generic

from apps.games.models import Game, Price, GameImage, Region, Platform


def index(request):
    latest_releases = Game.objects.exclude(
        title__isnull=True
    ).exclude(
        title__exact=""
    ).exclude(
        release_date__exact=None
    ).filter(
     release_date__lte=timezone.now()
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

    total_games = Game.objects.exclude(title__isnull=True).exclude(title__exact="").count()
    total_regions = Region.objects.all().count()
    total_platforms = Platform.objects.all().count()

    context = {
        'latest_releases': latest_releases,
        'discounted_games': discounted_games,
        'total_games': total_games,
        'total_regions': total_regions,
        'total_platforms': total_platforms,
    }
    return render(request, 'games/index.html', context)


class GameListView(generic.ListView):
    model = Game
    template_name = 'games/game_list.html'
    context_object_name = 'game_list'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().exclude(title__exact="").exclude(title__isnull=True)

        # Filters
        discounted = self.request.GET.get('discounted')
        release_year = self.request.GET.get('release_year')

        if discounted == 'true':
            qs = qs.filter(prices__discount_percentage__gt=0, prices__is_on_sale=True)
        elif discounted == 'false':
            qs = qs.filter(Q(prices__is_on_sale=False) | Q(prices__isnull=True))

        if release_year:
            qs = qs.filter(release_date__year=release_year)

        # Ordering
        ordering = self.request.GET.get('ordering')

        if ordering == 'title':
            qs = qs.order_by(Lower('title'))
        elif ordering == '-title':
            qs = qs.order_by(Lower('title')).reverse()
        elif ordering == 'discount':
            qs = qs.order_by('-prices__discount_percentage')
        elif ordering == 'release_date':
            qs = qs.order_by(F('release_date').asc(nulls_last=True))
        elif ordering == '-release_date' or not ordering:
            qs = qs.order_by(F('release_date').desc(nulls_last=True))
        else:
            qs = qs.order_by(F('release_date').desc(nulls_last=True))

        return qs.distinct()

    def get(self, request, *args, **kwargs):
        params = request.GET.copy()
        changed = False

        if 'discounted' in params and not params['discounted']:
            params.pop('discounted')
            changed = True
        if 'release_year' in params and not params['release_year']:
            params.pop('release_year')
            changed = True
        if 'ordering' in params and params['ordering'] == '-release_date':
            params.pop('ordering')
            changed = True

        if changed:
            qs = params.urlencode()
            return redirect(f"{request.path}?{qs}" if qs else request.path)

        return super().get(request, *args, **kwargs)


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


def about(request):
    return render(request, 'games/about.html')