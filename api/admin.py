from django.contrib import admin
from api.models import Stock, News, PriceHistory, NewsSentimentHistory


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['ticker', 'company_full_name', 'current_price', 'change_in_day', 'sentiment_score', 'updated_at']
    list_filter = ['updated_at', 'sentiment_score']
    search_fields = ['ticker', 'company_full_name']


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['ticker', 'title', 'source', 'date', 'sentiment', 'sentiment_analyzed']
    list_filter = ['ticker', 'sentiment', 'sentiment_analyzed', 'date']
    search_fields = ['ticker', 'title', 'content']
    readonly_fields = ['id']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'price', 'volume']
    list_filter = ['date', 'stock']
    search_fields = ['stock__ticker']


@admin.register(NewsSentimentHistory)
class NewsSentimentHistoryAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'bullish_count', 'bearish_count', 'neutral_count', 'total_news']
    list_filter = ['date', 'stock']
    search_fields = ['stock__ticker']

