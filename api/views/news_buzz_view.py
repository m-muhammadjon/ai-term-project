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
    """API endpoint to get most mentioned stocks in news"""
    
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
        
        # Calculate date range based on time_period
        now = timezone.now()
        if time_period == '1d':
            start_date = now - timedelta(days=1)
        elif time_period == '7d':
            start_date = now - timedelta(days=7)
        elif time_period == '30d':
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)  # Default to 7 days
        
        # Get news counts per ticker from database
        news_counts = News.objects.filter(
            date__gte=start_date
        ).values('ticker').annotate(
            news_count=Count('id')
        ).order_by('-news_count')
        
        # Get all stocks for company names
        stocks_dict = {stock.ticker: stock for stock in Stock.objects.all()}
        
        # Calculate buzz scores
        buzz_data = []
        max_news_count = 0
        
        # First pass: find max count for normalization
        for item in news_counts:
            if item['news_count'] > max_news_count:
                max_news_count = item['news_count']
        
        # Second pass: calculate scores
        for item in news_counts:
            ticker = item['ticker']
            news_count = item['news_count']
            
            # Normalize score (0.0 to 0.999999)
            # Score is based on relative news count
            if max_news_count > 0:
                score = min(news_count / max(max_news_count, 10.0), 0.999999)
            else:
                score = 0.0
            
            # Get company name from Stock model or use fallback
            stock = stocks_dict.get(ticker)
            if stock and stock.company_full_name:
                company_full_name = stock.company_full_name
            else:
                # Fallback to a simple name
                company_full_name = f'{ticker} Corporation'
            
            buzz_data.append({
                'ticker': ticker,
                'score': round(score, 6),
                'company_full_name': company_full_name
            })
        
        # Sort by score (already sorted by news_count, but ensure score order)
        buzz_data.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit results
        buzz_data = buzz_data[:limit]
        
        serializer = NewsBuzzSerializer(buzz_data, many=True)
        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)

