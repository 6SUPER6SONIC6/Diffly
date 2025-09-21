from django.shortcuts import render
from django.views import generic

from apps.games.models import Game


def index(request):
    recently_added_games = Game.objects.exclude(title__isnull=True).exclude(title__exact="").order_by('-created_at')[:5]
    context = {'recently_added_games': recently_added_games}
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


    def get_queryset(self):
        query = self.request.GET.get('q')
        queryset = Game.objects.exclude(title__isnull=True).exclude(title__exact="").order_by('title')
        if query:
            return queryset.filter(title__icontains=query)
        else:
            return None
