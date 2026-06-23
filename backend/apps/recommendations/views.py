"""
AIU — Recommendations App: Views (re-export from models file for clean import)
"""
from apps.recommendations.models import RecommendationViewSet, RecommendationSerializer

__all__ = ["RecommendationViewSet", "RecommendationSerializer"]
