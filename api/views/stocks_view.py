from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.models import Stock
from api.serializers.stock_serializers import StockSerializer


class StocksView(APIView):
    """API endpoint to get all stocks"""
    
    @extend_schema(
        summary="Get all stocks",
        description="Returns a list of all stocks with their current information",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of stocks to return',
                required=False,
                default=50
            ),
        ],
        responses={200: StockSerializer(many=True)},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        
        stocks = Stock.objects.all()[:limit]
        serializer = StockSerializer(stocks, many=True)
        
        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)

