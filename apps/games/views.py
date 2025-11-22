from django.db.models import Prefetch, Q, F, Max, Case, When, Value
from django.db.models.fields import DecimalField
from django.db.models.functions import Lower, ExtractYear, Cast
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import generic

from apps.games.models import Game, Price, GameImage, Region, Platform, Subscription, Genre


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
    ).order_by('-release_date')[:16]

    discounted_games = Game.objects.exclude(
        title__isnull=True
    ).exclude(
        title__exact=""
    ).filter(
        prices__current_price__lt=F('prices__base_price'),
    ).annotate(
        max_discount=Max(
            Cast(
                (F('prices__base_price') - F('prices__current_price')) / F('prices__base_price') * 100,
                DecimalField(max_digits=10, decimal_places=2)
            ))
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
                current_price__lt=F('base_price')
            ).select_related('region')
        ),
        'subscriptions'
    ).order_by('-max_discount').distinct()[:16]

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        release_years = (
            Game.objects.exclude(release_date__isnull=True)
            .annotate(year=ExtractYear('release_date'))
            .values_list('year', flat=True)
            .distinct()
            .order_by('-year')
        )
        context['release_years'] = release_years

        context['all_subscriptions'] = Subscription.objects.all().order_by('title')
        context['selected_subscription'] = self.request.GET.get('subscription', '')

        context['all_genres'] = Genre.objects.all().order_by('title')
        context['selected_genre'] = self.request.GET.get('genre', '')
        return context

    def get_queryset(self):
        qs = super().get_queryset().exclude(title__exact="").exclude(title__isnull=True)

        # Filters
        discounted = self.request.GET.get('discounted')
        release_year = self.request.GET.get('release_year')
        subscription_title = self.request.GET.get('subscription')
        genre_title = self.request.GET.get('genre')

        if discounted == 'true':
            qs = qs.filter(
                prices__current_price__lt=F('prices__base_price'),
            ).distinct()
        elif discounted == 'false':
            qs = qs.filter(
                Q(prices__current_price__gte=F('prices__base_price')) |
                Q(prices__isnull=True)
            ).distinct()

        if release_year:
            qs = qs.filter(release_date__year=release_year)

        if subscription_title:
            qs = qs.filter(subscriptions__title__icontains=subscription_title)

        if genre_title:
            qs = qs.filter(genres__title=genre_title)

        # Ordering
        ordering = self.request.GET.get('ordering')

        if ordering == 'title':
            qs = qs.order_by(Lower('title'))
        elif ordering == '-title':
            qs = qs.order_by(Lower('title')).reverse()
        elif ordering == 'discount':
            qs = qs.annotate(
                max_discount=Max(
                    Case(
                        When(
                            Q(prices__base_price__gt=0) & Q(prices__current_price__lt=F('prices__base_price')),
                            then=Cast(
                                (F('prices__base_price') - F('prices__current_price')) / F('prices__base_price') * 100,
                                DecimalField(max_digits=10, decimal_places=2)
                            )
                        ),
                        default=Value(0),
                        output_field=DecimalField(max_digits=10, decimal_places=2)
                    )
                )
            ).order_by('-max_discount', 'title')
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
        if 'subscription' in params and not params['subscription']:
            params.pop('subscription')
            changed = True
        if 'genre' in params and not params['genre']:
            params.pop('genre')
            changed = True

        if changed:
            qs = params.urlencode()
            return redirect(f"{request.path}?{qs}" if qs else request.path)

        return super().get(request, *args, **kwargs)


class GameDetailView(generic.DetailView):
    model = Game
    template_name = 'games/game_detail.html'
    pk_url_kwarg = 'pk'
    slug_url_kwarg = 'slug'

    def get(self, request, *args, **kwargs):
        self.object = get_object_or_404(Game, pk=self.kwargs['pk'])

        if self.object.slug != self.kwargs['slug']:
            return redirect(self.object.get_absolute_url(), permanent=True)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


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
