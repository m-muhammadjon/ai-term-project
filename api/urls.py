from django.urls import path
from api.views import (
    TopMoversView,
    NewsBuzzView,
    SentimentMoversView,
    StocksView,
    NewsView,
    SentimentView,
    StockDetailsView
)

urlpatterns = [
    path('topMovers', TopMoversView.as_view(), name='top-movers'),
    path('newsBuzz', NewsBuzzView.as_view(), name='news-buzz'),
    path('sentimentMovers', SentimentMoversView.as_view(), name='sentiment-movers'),
    path('stocks', StocksView.as_view(), name='stocks'),
    path('news', NewsView.as_view(), name='news'),
    path('sentiment/<uuid:id>', SentimentView.as_view(), name='sentiment'),
    path('stock-details', StockDetailsView.as_view(), name='stock-details'),
]

