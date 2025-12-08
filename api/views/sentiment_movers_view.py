from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.models import Stock, News
from api.serializers.stock_serializers import SentimentMoverSerializer
from api.services.stock_api_service import StockAPIService


class SentimentMoversView(APIView):
    """API endpoint to get sentiment movers"""
    
    @extend_schema(
        summary="Get sentiment movers",
        description="Returns stocks with significant sentiment changes based on news analysis",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of sentiment movers to return',
                required=False,
                default=10
            ),
        ],
        responses={200: SentimentMoverSerializer(many=True)},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        # Get stocks with recent news
        stocks = Stock.objects.all()[:limit * 3]
        
        sentiment_movers = []
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        for stock in stocks:
            # Calculate current sentiment score (last 24 hours)
            recent_news = News.objects.filter(
                ticker=stock.ticker,
                date__date__gte=yesterday,
                sentiment_analyzed=True
            )
            
            if recent_news.exists():
                bullish = recent_news.filter(sentiment='Bullish').count()
                bearish = recent_news.filter(sentiment='Bearish').count()
                neutral = recent_news.filter(sentiment='Neutral').count()
                total = bullish + bearish + neutral
                
                if total > 0:
                    # Calculate sentiment score: -100 (all bearish) to +100 (all bullish)
                    sentiment_score = int(((bullish - bearish) / total) * 100)
                    
                    # Calculate change from previous period (last week)
                    previous_news = News.objects.filter(
                        ticker=stock.ticker,
                        date__date__gte=week_ago,
                        date__date__lt=yesterday,
                        sentiment_analyzed=True
                    )
                    
                    prev_bullish = previous_news.filter(sentiment='Bullish').count()
                    prev_bearish = previous_news.filter(sentiment='Bearish').count()
                    prev_total = prev_bullish + prev_bearish + previous_news.filter(sentiment='Neutral').count()
                    
                    if prev_total > 0:
                        prev_sentiment_score = int(((prev_bullish - prev_bearish) / prev_total) * 100)
                        change = sentiment_score - prev_sentiment_score
                    else:
                        change = 0
                    
                    sentiment_movers.append({
                        'ticker': stock.ticker,
                        'sentiment_score': sentiment_score,
                        'change': change
                    })
        
        # Sort by absolute change (biggest movers first)
        sentiment_movers.sort(key=lambda x: abs(x['change']), reverse=True)
        sentiment_movers = sentiment_movers[:limit]
        
        serializer = SentimentMoverSerializer(sentiment_movers, many=True)
        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)

