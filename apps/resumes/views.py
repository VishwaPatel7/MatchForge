from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from apps.resumes.models import CandidateResume
from apps.resumes.serializers import CandidateResumeSerializer
from apps.resumes.services import ResumeParsingService


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('resume')
        if not file_obj:
            return Response({"error": "No file uploaded. Please attach a PDF resume under key 'resume'."}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj.name.lower().endswith('.pdf'):
            return Response({"error": "Invalid format. Only PDF files are accepted."}, status=status.HTTP_400_BAD_REQUEST)

        if file_obj.size > 5 * 1024 * 1024:
            return Response({"error": "File size exceeds 5MB limit."}, status=status.HTTP_400_BAD_REQUEST)

        profile = request.user.profile

        # Create resume instance
        resume = CandidateResume.objects.create(
            profile=profile,
            file=file_obj,
            file_name=file_obj.name,
            file_size=file_obj.size,
            is_active=True
        )

        # Deactivate any previous resumes for this profile
        CandidateResume.objects.filter(profile=profile).exclude(id=resume.id).update(is_active=False)

        # Execute extraction service
        try:
            ResumeParsingService.process_resume(resume)
            serializer = CandidateResumeSerializer(resume)
            return Response({
                "status": "success",
                "message": "Resume uploaded and parsed successfully.",
                "resume": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "status": "partial_success",
                "message": "Resume uploaded but text parsing encountered an error.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LatestResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        resume = CandidateResume.objects.filter(profile=profile, is_active=True).first()
        if not resume:
            return Response({"message": "No active resume uploaded yet."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CandidateResumeSerializer(resume)
        return Response(serializer.data)
