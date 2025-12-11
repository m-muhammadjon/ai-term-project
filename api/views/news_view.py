from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.models import News
from api.serializers.stock_serializers import NewsSerializer
from api.services.news_service import NewsService


class NewsView(APIView):
    
    @extend_schema(
        summary="Get news articles",
        description="Returns news articles with optional filtering by sentiment, stocks, and time period",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of news articles to return',
                required=False,
                default=20
            ),
            OpenApiParameter(
                name='sentiment',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter by sentiment: Bullish, Bearish, or Neutral',
                required=False,
                enum=['Bullish', 'Bearish', 'Neutral']
            ),
            OpenApiParameter(
                name='stocks',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Comma-separated list of stock tickers (e.g., "AAPL,MSFT")',
                required=False
            ),
            OpenApiParameter(
                name='timePeriod',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Time period: 1d, 7d, or 30d',
                required=False,
                default='7d',
                enum=['1d', '7d', '30d']
            ),
        ],
        responses={200: NewsSerializer(many=True)},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        sentiment = request.query_params.get('sentiment', None)
        stocks = request.query_params.get('stocks', None)
        time_period = request.query_params.get('timePeriod', '7d')
        
        ticker_list = None
        if stocks:
            ticker_list = [t.strip().upper() for t in stocks.split(',')]
        
        if time_period == '1d':
            start_date = datetime.now() - timedelta(days=1)
        elif time_period == '7d':
            start_date = datetime.now() - timedelta(days=7)
        elif time_period == '30d':
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(days=7)
        
        news_queryset = News.objects.filter(date__gte=start_date)
        
        if ticker_list:
            news_queryset = news_queryset.filter(ticker__in=ticker_list)
        
        if sentiment:
            news_queryset = news_queryset.filter(sentiment=sentiment)
        
        news_count = news_queryset.count()
        
        if news_count < limit and ticker_list:
            news_service = NewsService()
            for ticker in ticker_list[:3]:
                external_news = news_service.get_news_for_ticker(
                    ticker, 
                    limit=limit // len(ticker_list) if ticker_list else limit,
                    sentiment=sentiment,
                    time_period=time_period
                )
                
                for article in external_news:
                    News.objects.update_or_create(
                        link=article['link'],
                        defaults={
                            'ticker': article['ticker'],
                            'title': article['title'],
                            'content': article['content'],
                            'source': article['source'],
                            'author': article.get('author'),
                            'date': article['date'],
                            'sentiment': article.get('sentiment'),
                            'sentiment_analyzed': article.get('sentiment') is not None
                        }
                    )
        
        news_queryset = News.objects.filter(date__gte=start_date)
        if ticker_list:
            news_queryset = news_queryset.filter(ticker__in=ticker_list)
        if sentiment:
            news_queryset = news_queryset.filter(sentiment=sentiment)
        news_queryset = news_queryset.order_by('-date')[:limit]
        
        serializer = NewsSerializer(news_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

