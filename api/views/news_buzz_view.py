from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.services.news_service import NewsService
from api.serializers.stock_serializers import NewsBuzzSerializer


class NewsBuzzView(APIView):
    """API endpoint to get most mentioned stocks in news"""
    
    @extend_schema(
        summary="Get news buzz",
        description="Returns most mentioned stocks in news with their buzz scores",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of stocks to return',
                required=False,
                default=10
            ),
        ],
        responses={200: NewsBuzzSerializer(many=True)},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        news_service = NewsService()
        buzz_data = news_service.get_news_buzz(limit=limit)
        
        serializer = NewsBuzzSerializer(buzz_data, many=True)
        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)

