from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.models import Stock, PriceHistory, NewsSentimentHistory, News
from api.serializers.stock_serializers import StockDetailsSerializer, NewsSentimentHistorySerializer, NewsSerializer
from api.services.stock_api_service import StockAPIService
from api.services.news_service import NewsService


class StockDetailsView(APIView):
    
    QUOTE_CACHE_DURATION = 3600
    
    @extend_schema(
        summary="Get stock details",
        description="Returns comprehensive information about a stock including price history, news sentiment, and recent news",
        parameters=[
            OpenApiParameter(
                name='ticker',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Stock ticker symbol (e.g., AAPL, MSFT)',
                required=True
            ),
        ],
        responses={200: StockDetailsSerializer},
    )
    def get(self, request):
        ticker = request.query_params.get('ticker', '').upper()
        
        if not ticker:
            return Response(
                {'error': 'Ticker parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock, created = Stock.objects.get_or_create(
                ticker=ticker,
                defaults={'company_full_name': f'{ticker} Corporation'}
            )
            
            stock_service = StockAPIService()
            now = datetime.now()
            
            should_update_quote = self._should_update_stock_quote(stock, now)
            
            if should_update_quote:
                quote = stock_service.get_stock_quote(ticker)
                if quote:
                    stock.current_price = quote['current_price']
                    stock.change_in_day = quote['change_percent']
                    if quote.get('market_cap'):
                        stock.market_cap = quote['market_cap']
                    if quote.get('volume'):
                        stock.volume = quote['volume']
                    stock.save()
            
            if not stock.company_full_name or stock.company_full_name == f'{ticker} Corporation':
                news_service = NewsService()
            
            today = now.date()
            start_date = today - timedelta(days=30)
            
            existing_history = PriceHistory.objects.filter(
                stock=stock,
                date__gte=start_date
            ).values_list('date', flat=True)
            existing_dates = set(existing_history)
            
            required_dates = set()
            for i in range(30):
                date = start_date + timedelta(days=i)
                required_dates.add(date)
            
            missing_dates = required_dates - existing_dates
            
            if missing_dates:
                oldest_missing = min(missing_dates)
                days_to_fetch = (today - oldest_missing).days + 1
                
                price_history_data = stock_service.get_price_history(ticker, days=days_to_fetch)
                
                for price_data in price_history_data:
                    if price_data['date'] in missing_dates:
                        PriceHistory.objects.update_or_create(
                            stock=stock,
                            date=price_data['date'],
                            defaults={
                                'price': price_data['price'],
                                'volume': price_data.get('volume', 0)
                            }
                        )
            
            price_history = PriceHistory.objects.filter(
                stock=stock,
                date__gte=start_date
            ).order_by('date')[:30]
            prices_history_list = [float(ph.price) for ph in price_history]
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            news_with_sentiment = News.objects.filter(
                ticker=ticker,
                date__date__gte=start_date,
                sentiment_analyzed=True
            )
            
            total_bullish = news_with_sentiment.filter(sentiment='Bullish').count()
            total_bearish = news_with_sentiment.filter(sentiment='Bearish').count()
            total_neutral = news_with_sentiment.filter(sentiment='Neutral').count()
            
            news_sentiment_data = {
                'bullish': total_bullish,
                'bearish': total_bearish,
                'neutral': total_neutral
            }
            
            news_sentiment_serializer = NewsSentimentHistorySerializer(news_sentiment_data)
            
            recent_news = News.objects.filter(ticker=ticker).order_by('-date')[:10]
            recent_news_serializer = NewsSerializer(recent_news, many=True)
            
            total_news = News.objects.filter(ticker=ticker).count()
            news_buzz_score = min(total_news / 100.0, 0.999999)
            
            market_cap_str = self._format_number(stock.market_cap) if stock.market_cap else 'N/A'
            volume_str = self._format_number(stock.volume) if stock.volume else 'N/A'
            
            response_data = {
                'companyFullName': stock.company_full_name,
                'price': float(stock.current_price) if stock.current_price else 0.0,
                'changeInDay': float(stock.change_in_day) if stock.change_in_day else 0.0,
                'marketCap': market_cap_str,
                'volume': volume_str,
                'newsBuzz': f"{news_buzz_score:.6f}",
                'pricesHistory': prices_history_list,
                'newsSentiment': news_sentiment_serializer.data,
                'recentNews': recent_news_serializer.data
            }
            
            serializer = StockDetailsSerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _should_update_stock_quote(self, stock, now):
        if not stock.updated_at:
            return True
        
        if stock.updated_at.tzinfo:
            time_since_update = now - stock.updated_at.replace(tzinfo=None)
        else:
            time_since_update = now - stock.updated_at
        
        if time_since_update.total_seconds() > self.QUOTE_CACHE_DURATION:
            return True
        
        if not stock.current_price:
            return True
        
        return False
    
    def _format_number(self, num):
        if num is None:
            return 'N/A'
        
        if num >= 1_000_000_000_000:
            return f"${num / 1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num / 1_000:.2f}K"
        else:
            return f"${num}"

