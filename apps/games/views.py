from django.http import HttpResponse


def index(request):
    return HttpResponse("Homepage")


def games(request):
    return HttpResponse("Games list")


def game_detail(request, game_id):
    return HttpResponse("Game detail")
