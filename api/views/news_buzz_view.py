from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.models import News, Stock
from api.serializers.stock_serializers import NewsBuzzSerializer


class NewsBuzzView(APIView):
    
    @extend_schema(
        summary="Get news buzz",
        description="Returns most mentioned stocks in news with their buzz scores based on database",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of stocks to return',
                required=False,
                default=10
            ),
            OpenApiParameter(
                name='timePeriod',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Time period: 1d, 7d, or 30d (default: 7d)',
                required=False,
                enum=['1d', '7d', '30d']
            ),
        ],
        responses={200: NewsBuzzSerializer(many=True)},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        time_period = request.query_params.get('timePeriod', '7d')
        
        now = timezone.now()
        if time_period == '1d':
            start_date = now - timedelta(days=1)
        elif time_period == '7d':
            start_date = now - timedelta(days=7)
        elif time_period == '30d':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)
        
        news_counts = News.objects.filter(
            date__gte=start_date
        ).values('ticker').annotate(
            news_count=Count('id')
        ).order_by('-news_count')
        
        stocks_dict = {stock.ticker: stock for stock in Stock.objects.all()}
        
        buzz_data = []
        max_news_count = 0
        
        for item in news_counts:
            if item['news_count'] > max_news_count:
                max_news_count = item['news_count']
        
        for item in news_counts:
            ticker = item['ticker']
            news_count = item['news_count']
            
            if max_news_count > 0:
                score = min(news_count / max(max_news_count, 10.0), 0.999999)
            else:
                score = 0.0
            
            stock = stocks_dict.get(ticker)
            if stock and stock.company_full_name:
                company_full_name = stock.company_full_name
            else:
                company_full_name = f'{ticker} Corporation'
            
            buzz_data.append({
                'ticker': ticker,
                'score': round(score, 6),
                'company_full_name': company_full_name
            })
        
        buzz_data.sort(key=lambda x: x['score'], reverse=True)
        
        buzz_data = buzz_data[:limit]
        
        serializer = NewsBuzzSerializer(buzz_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

