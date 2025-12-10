from rest_framework import serializers
from api.models import Stock, News, PriceHistory, NewsSentimentHistory


class TopMoverSerializer(serializers.Serializer):
    """Serializer for top movers response"""
    ticker = serializers.CharField()
    change = serializers.DecimalField(max_digits=10, decimal_places=2)
    currentPrice = serializers.DecimalField(max_digits=10, decimal_places=2, source='current_price')


class NewsBuzzSerializer(serializers.Serializer):
    """Serializer for news buzz response"""
    ticker = serializers.CharField()
    score = serializers.DecimalField(max_digits=10, decimal_places=6)
    companyFullName = serializers.CharField(source='company_full_name')


class SentimentMoverSerializer(serializers.Serializer):
    """Serializer for sentiment movers response"""
    ticker = serializers.CharField()
    sentimentScore = serializers.IntegerField(source='sentiment_score')
    change = serializers.IntegerField()


class StockSerializer(serializers.ModelSerializer):
    """Serializer for stocks list"""
    ticker = serializers.CharField()
    companyFullName = serializers.CharField(source='company_full_name')
    changeInDay = serializers.DecimalField(max_digits=10, decimal_places=2, source='change_in_day')
    currentPrice = serializers.DecimalField(max_digits=10, decimal_places=2, source='current_price')
    sentimentScore = serializers.IntegerField(source='sentiment_score', allow_null=True)
    
    class Meta:
        model = Stock
        fields = ['ticker', 'companyFullName', 'changeInDay', 'currentPrice', 'sentimentScore']


class NewsSerializer(serializers.ModelSerializer):
    """Serializer for news articles"""
    id = serializers.UUIDField()
    ticker = serializers.CharField()
    title = serializers.CharField()
    content = serializers.CharField()
    source = serializers.CharField()
    author = serializers.CharField(allow_null=True)
    date = serializers.DateTimeField()
    link = serializers.URLField()
    sentiment = serializers.CharField(allow_null=True, required=False)
    sentimentAnalyzed = serializers.BooleanField(source='sentiment_analyzed', required=False)
    
    class Meta:
        model = News
        fields = ['id', 'ticker', 'title', 'content', 'source', 'author', 'date', 'link', 'sentiment', 'sentimentAnalyzed']


class SentimentResponseSerializer(serializers.Serializer):
    """Serializer for sentiment analysis response"""
    sentiment = serializers.CharField()


class PriceHistorySerializer(serializers.ModelSerializer):
    """Serializer for price history"""
    date = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = PriceHistory
        fields = ['date', 'price']


class NewsSentimentHistorySerializer(serializers.Serializer):
    """Serializer for news sentiment history"""
    date = serializers.DateField()
    bullish = serializers.IntegerField()
    bearish = serializers.IntegerField()
    neutral = serializers.IntegerField()


class StockDetailsSerializer(serializers.Serializer):
    """Serializer for stock details response"""
    companyFullName = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    changeInDay = serializers.DecimalField(max_digits=10, decimal_places=2)
    marketCap = serializers.CharField()
    volume = serializers.CharField()
    newsBuzz = serializers.CharField()
    pricesHistory = PriceHistorySerializer(many=True)
    newsSentiment = NewsSentimentHistorySerializer(many=True)
    recentNews = NewsSerializer(many=True)

