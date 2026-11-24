from django.urls import path
from apps.resumes.views import ResumeUploadView, LatestResumeView

urlpatterns = [
    path('resumes/upload/', ResumeUploadView.as_view(), name='api-resume-upload'),
    path('resumes/latest/', LatestResumeView.as_view(), name='api-resume-latest'),
]
