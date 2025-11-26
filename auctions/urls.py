from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("bid/<int:listing_id>", views.bid, name="bid"),
    path("close", views.close, name="close"),
    path("comment/<int:listing_id>", views.comment, name="comment"),
    path("listing/<int:id>", views.listing, name="listing"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("new", views.new, name="new"),
    path("register", views.register, name="register"),
    path("watchlist", views.watchlist, name="watchlist"),
]
