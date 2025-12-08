from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from api.services.stock_api_service import StockAPIService
from api.serializers.stock_serializers import TopMoverSerializer


class TopMoversView(APIView):
    """API endpoint to get top movers"""
    
    @extend_schema(
        summary="Get top movers",
        description="Returns stocks with the highest price changes",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of top movers to return',
                required=False,
                default=10
            ),
        ],
        responses={200: TopMoverSerializer(many=True)},
    )
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        stock_service = StockAPIService()
        movers = stock_service.get_top_movers(limit=limit)
        
        serializer = TopMoverSerializer(movers, many=True)
        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)

