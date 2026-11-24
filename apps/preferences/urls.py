from django.urls import path
from apps.preferences.views import PreferenceListView, PreferenceHistoryView

urlpatterns = [
    path('preferences/', PreferenceListView.as_view(), name='api-preferences'),
    path('preferences/history/', PreferenceHistoryView.as_view(), name='api-preferences-history'),
]
