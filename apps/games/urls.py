from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("games/", views.GameListView.as_view(), name="games"),
    path("games/<int:pk>/", views.GameDetailView.as_view(), name="game_detail"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("about/", views.about, name="about"),
]