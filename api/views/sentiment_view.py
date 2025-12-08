from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.models import News
from api.serializers.stock_serializers import SentimentResponseSerializer
from api.services.sentiment_service import SentimentService
import uuid


class SentimentView(APIView):
    """API endpoint to get sentiment analysis for a specific news article"""
    
    @extend_schema(
        summary="Get sentiment analysis",
        description="Returns sentiment analysis (Bullish, Bearish, or Neutral) for a specific news article by UUID",
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description='UUID of the news article',
                required=True
            ),
        ],
        responses={
            200: SentimentResponseSerializer,
            404: {'description': 'News article not found'},
            400: {'description': 'Invalid UUID format'}
        },
    )
    def get(self, request, id):
        try:
            # Validate UUID
            news_id = uuid.UUID(str(id))
            
            # Get news article
            try:
                news = News.objects.get(id=news_id)
            except News.DoesNotExist:
                return Response(
                    {'error': 'News article not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # If sentiment already analyzed, return it
            if news.sentiment_analyzed and news.sentiment:
                return Response({
                    'data': {
                        'sentiment': news.sentiment
                    }
                }, status=status.HTTP_200_OK)
            
            # Analyze sentiment
            sentiment_service = SentimentService()
            text_to_analyze = f"{news.title} {news.content}"
            sentiment_result = sentiment_service.analyze_sentiment(text_to_analyze)
            
            # Update news article with sentiment
            news.sentiment = sentiment_result['sentiment']
            news.sentiment_analyzed = True
            news.save()
            
            serializer = SentimentResponseSerializer(sentiment_result)
            return Response({
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response(
                {'error': 'Invalid UUID format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

