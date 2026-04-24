"""
AIU — Memory App: Views
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MemoryInsight
from .serializers import ConversationSerializer, MessageSerializer, MemoryInsightSerializer


class InsightListView(APIView):
    """
    GET /api/v1/memory/insights/
    GET /api/v1/memory/insights/?type=behavior
    Returns all active insights for the authenticated user.
    """

    def get(self, request):
        insight_type = request.query_params.get("type")
        qs = MemoryInsight.objects.filter(user=request.user, is_active=True)

        if insight_type:
            qs = qs.filter(insight_type=insight_type)

        qs = qs.order_by("-confidence")

        return Response({
            "status":  "success",
            "count":   qs.count(),
            "results": MemoryInsightSerializer(qs, many=True).data,
        })
