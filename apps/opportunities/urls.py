from django.urls import path
from apps.opportunities.views import (
    OpportunityListView,
    OpportunityDetailView,
    OpportunitySearchView,
    OpportunityCompareView,
    SavedOpportunityToggleView
)

urlpatterns = [
    path('opportunities/', OpportunityListView.as_view(), name='api-opportunity-list'),
    path('opportunities/<uuid:id>/', OpportunityDetailView.as_view(), name='api-opportunity-detail'),
    path('opportunities/search/', OpportunitySearchView.as_view(), name='api-opportunity-search'),
    path('opportunities/compare/', OpportunityCompareView.as_view(), name='api-opportunity-compare'),
    path('opportunities/<uuid:id>/save/', SavedOpportunityToggleView.as_view(), name='api-opportunity-save-toggle'),
    path('saved-opportunities/', SavedOpportunityToggleView.as_view(), name='api-saved-opportunities-list'),
]
